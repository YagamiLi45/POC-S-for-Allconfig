import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

# Configure Gemini
gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)

# Configure Pinecone
pinecone_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_key)

# Configure Jenkins
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


def get_console_output():
    """Fetch Jenkins console output from the last build."""
    url = f"{jenkins_url}/job/{job_name}/lastBuild/consoleText"
    response = requests.get(url, auth=HTTPBasicAuth(jenkins_user, jenkins_api_token))
    if response.status_code == 200:
        return response.text
    else:
        return f"Failed to fetch logs: {response.status_code}"


def extract_errors(log_text):
    """Extract only error/warning/failure lines."""
    errors = []
    for line in log_text.splitlines():
        if "ERROR" in line or "FAILURE" in line or "WARNING" in line:
            errors.append(line)
    return errors


def chunk_text(text, chunk_size=200):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


def embed_query(query):
    response = genai.embed_content(model="models/gemini-embedding-001", content=query)
    return response["embedding"] if isinstance(response, dict) else response


def retrieve_solution(query, threshold=0.7, top_k=3):
    query_vector = embed_query(query)
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    matches = []
    for match in results.matches:
        if match.score >= threshold:
            matches.append((match.metadata["text"], match.score))
    return matches


def generate_solution_gemini(error_message):
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(contents=error_message)
    return response.text


# === CLI Mode ===
def run_cli():
    print("=== Jenkins Error Resolver Retriever ===")
    while True:
        error_message = input("\nEnter Jenkins build error (or 'exit' to quit): ")
        if error_message.lower() in ["exit", "quit"]:
            break
        matches = retrieve_solution(error_message)
        if matches:
            print("\nFound similar solution(s) in Pinecone DB:")
            for text, score in matches:
                print(f"Score: {score:.3f}\nSolution: {text}\n")
        else:
            print("\nNo similar solution found. Generating via Gemini AI...")
            solution = generate_solution_gemini(error_message)
            print("Generated Solution:\n", solution)


# === Streamlit Web UI ===
def run_streamlit():
    st.title("🚀 Jenkins Error Resolver (Console + Pinecone + Gemini)")

    if st.button("Fetch & Resolve Jenkins Errors"):
        log_text = get_console_output1()          # Fetch Jenkins console output

        if log_text.startswith("Failed to fetch"):
            st.error(log_text)
        else:
            extracted = extract_errors(log_text) # Fetch and extract errors
            print("Extracted Errors:\n", extracted)

            if not extracted:
                st.info("✅ No errors/warnings/failures found in Jenkins logs.")
            else:
                st.subheader("📋 Extracted Errors/Warnings/Failures:")
                error_block = "\n".join(extracted)
                st.code(error_block)

                st.subheader("🔍 Resolving...")

                # Query Pinecone with the entire error block
                matches = retrieve_solution(error_block)

                if matches:
                    st.success("✅ Found similar solution(s) in Pinecone DB:")
                    for text, score in matches:
                        st.markdown(f"- **Score:** {score:.3f}\n{text}\n\n---")
                else:
                    st.warning("🤖 No similar solution found. Generating via Gemini...")
                    solution = generate_solution_gemini(error_block)
                    st.write(solution)


if __name__ == "__main__":
    mode = os.getenv("MODE", "web")  # default CLI, set MODE=web for streamlit
    if mode == "web":
        run_streamlit()
    else:
        run_cli()
