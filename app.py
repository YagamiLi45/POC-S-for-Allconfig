import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# Configure Gemini
gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)

# Configure Pinecone
pinecone_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_key)

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


# === Utility Functions ===
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
    st.title("🚀 Jenkins Error Resolver (Pinecone + Gemini)")
    error_message = st.text_area("Enter Jenkins build error:", "")
    if st.button("Resolve Error"):
        if error_message.strip():
            matches = retrieve_solution(error_message)
            if matches:
                st.subheader("✅ Found similar solution(s) in Pinecone DB:")
                for text, score in matches:
                    st.markdown(f"**Score:** {score:.3f}\n\n{text}\n\n---")
            else:
                st.subheader("🤖 No similar solution found. Generating via Gemini AI...")
                solution = generate_solution_gemini(error_message)
                st.write(solution)


if __name__ == "__main__":
    mode = os.getenv("MODE", "web")  # default CLI, set MODE=web for streamlit
    if mode == "web":
        run_streamlit()
    else:
        run_cli()
