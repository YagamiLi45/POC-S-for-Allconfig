import os
import sys
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
import requests
from requests.auth import HTTPBasicAuth
import re
import hashlib

load_dotenv()

# --- Configure Gemini ---
gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)

# --- Configure Pinecone ---
pinecone_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_key)

# --- Jenkins Config ---
jenkins_url = os.getenv("JENKINS_URL")
job_name = os.getenv("JOB_NAME")
jenkins_user = os.getenv("JENKINS_USER")
jenkins_api_token = os.getenv("JENKINS_API_TOKEN")

INDEX_NAME = "error-store"

# Create index if not exists
if INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=3072,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(INDEX_NAME)

# --- Fetch Jenkins console output ---
def get_console_output():
    url = f"{jenkins_url}/job/{job_name}/lastBuild/consoleText"
    response = requests.get(url, auth=HTTPBasicAuth(jenkins_user, jenkins_api_token))
    if response.status_code == 200:
        return response.text
    else:
        return f"Failed to fetch logs: {response.status_code}"

# --- Extract Errors ---
def extract_errors(log_text, fallback_lines=20):
    """
    Extract Jenkins errors as blocks of consecutive error lines.
    """
    log_lines = log_text.splitlines()
    error_blocks = []
    current_block = []

    patterns = [
        r"\bERROR\b",
        r"\bFAILURE\b",
        r"\bWARNING\b",
        r"\bEXCEPTION\b",
        r"\bTRACEBACK\b",
        r"^\s*at\s+.+",    # Java stack trace
        r"^ERROR:.*",      # Jenkins error lines
        r"^\[ERROR\].*",   # Maven/Gradle
        r"^\[WARNING\].*"
    ]
    combined = re.compile("|".join(patterns), re.IGNORECASE)

    for line in log_lines:
        if combined.search(line):
            current_block.append(line.strip())
        else:
            if current_block:
                # End of a block
                error_blocks.append("\n".join(current_block))
                current_block = []

    # Add last block if exists
    if current_block:
        error_blocks.append("\n".join(current_block))

    # If no errors found but build failed, fallback to last few lines
    if not error_blocks and "FINISHED: FAILURE" in log_text.upper():
        error_blocks.append("\n".join(log_lines[-fallback_lines:]))

    return error_blocks


# --- Embedding + Retrieval ---
def embed_query(query):
    response = genai.embed_content(model="models/gemini-embedding-001", content=query)
    return response["embedding"] if isinstance(response, dict) else response

def retrieve_solution(error_block, threshold=0.92, top_k=3):
    query_vector = embed_query(error_block)
    results = index.query(vector=query_vector, top_k=top_k, include_metadata=True)

    matches = [
        {
            "errors": match.metadata.get("errors", ""),
            "steps": match.metadata.get("steps", ""),
            "details": match.metadata.get("details", ""),
            "score": match.score
        }
        for match in results.matches if match.score >= threshold
    ]

    return matches

# --- Summarize Errors (for display only) ---
def summarize_errors_with_gemini(error_block):
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
    Summarize the following Jenkins errors in 5-6 clear lines.
    Make it easy to understand what went wrong without full stack traces.

    {error_block}
    """
    response = model.generate_content(prompt)
    return response.text.strip()

# --- Generate Gemini Solution ---
def generate_solution_gemini(error_message):
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
    The following Jenkins build failed with these errors:
    {error_message}

    Please provide a fix guide in two parts:
    1. Short actionable steps (numbered list).
    2. A longer explanation under 'More Details:'.

    Format strictly like:
    1. Step one...
    2. Step two...
    3. Step three...

    More Details:
    (explanation here)
    """
    response = model.generate_content(prompt)
    full_text = response.text.strip()

    parts = full_text.split("More Details:", 1)
    steps = parts[0].strip()
    details = parts[1].strip() if len(parts) > 1 else full_text

    return {"steps": steps, "details": details}

# --- Store in Pinecone ---
def store_solution_in_pinecone(raw_error, solution):
    item_id = hashlib.md5(raw_error.encode("utf-8")).hexdigest()
    embedding = embed_query(raw_error)

    index.upsert(
        vectors=[
            {
                "id": item_id,
                "values": embedding,
                "metadata": {
                    "errors": raw_error,
                    "steps": solution["steps"],
                    "details": solution["details"]
                },
            }
        ]
    )
    print(f"\n Solution saved/updated in Pinecone with ID {item_id}.", flush=True)

# --- CLI Mode ---
def run_cli():
    print("=== Jenkins Error Resolver (CLI Mode) ===", flush=True)

    log_text = get_console_output()
    if log_text.startswith("Failed to fetch"):
        print(log_text, flush=True)
        return

    extracted = extract_errors(log_text)
    if not extracted:
        print("No errors found in Jenkins logs.", flush=True)
        return

    error_block = "\n".join(extracted)

    # Summarize only for display
    summarized_errors = summarize_errors_with_gemini(error_block)
    print(" Summarized Errors:\n", summarized_errors, flush=True)

    matches = retrieve_solution(error_block)

    if matches:
        print("\n Found similar solution(s) in Pinecone DB:", flush=True)
        for match in matches:
            print(f"\n--- Raw Error (Score: {match['score']:.3f}) ---\n{match['errors']}", flush=True)
            print(f"\n--- Steps ---\n{match['steps']}", flush=True)
            if os.getenv("VERBOSE", "false").lower() == "true":
                print("\n--- More Details ---\n", match["details"], flush=True)
    else:
        print("\n No solution found in Pinecone. Generating with Gemini...", flush=True)
        solution = generate_solution_gemini(error_block)

        print("\n--- Steps ---\n", solution["steps"], flush=True)
        if os.getenv("VERBOSE", "false").lower() == "true":
            print("\n--- More Details ---\n", solution["details"], flush=True)

        store_solution_in_pinecone(error_block, solution)

    sys.stdout.flush()

# --- Web Mode (Streamlit UI) ---
def run_streamlit():
    st.title("🚀 Jenkins Error Resolver (Web UI)")

    if st.button("Fetch & Resolve Jenkins Errors"):
        log_text = get_console_output()
        if log_text.startswith("Failed to fetch"):
            st.error(log_text)
            return

        extracted = extract_errors(log_text)
        if not extracted:
            st.info("✅ No errors/warnings/failures found in Jenkins logs.")
            return

        error_block = "\n".join(extracted)

        # Summarize for display
        summarized_errors = summarize_errors_with_gemini(error_block)
        st.subheader("📋 Summarized Errors:")
        st.markdown(summarized_errors)

        st.subheader("🔍 Resolving...")
        matches = retrieve_solution(error_block)

        if matches:
            st.success("✅ Found similar solution(s) in Pinecone DB:")
            for match in matches:
                with st.expander(f"Solution (Score: {match['score']:.3f}) - Click to expand"):
                    # st.markdown("### Raw Error")
                    # st.markdown(match["errors"])
                    st.markdown("### Steps")
                    st.markdown(match["steps"])
                    if match["details"]:
                        st.markdown("### More Details")
                        st.markdown(match["details"])
        else:
            st.warning("🤖 No similar solution found. Generating via Gemini...")
            solution = generate_solution_gemini(error_block)

            st.subheader("🔧 Gemini Suggested Fix (Steps):")
            st.markdown(solution["steps"])

            with st.expander("Show More (Detailed Explanation)"):
                st.markdown(solution["details"])

            store_solution_in_pinecone(error_block, solution)
            st.success("✅ Solution saved/updated in Pinecone for future use.")

# --- Entry Point ---
if __name__ == "__main__":
    mode = os.getenv("MODE", "web")  # default = web, set MODE=cli for Jenkins
    if mode == "web":
        run_streamlit()
    else:
        run_cli()
