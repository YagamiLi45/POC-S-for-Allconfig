# import os
# from dotenv import load_dotenv
# import google.generativeai as genai
# from google.generativeai.types import ContentType
# from pinecone import Pinecone, ServerlessSpec

# # -----------------------------
# # 1. Load .env file
# # -----------------------------
# load_dotenv()

# # -----------------------------
# # 2. Configure Gemini AI
# # -----------------------------
# gemini_key = os.getenv("GEMINI_API_KEY")
# genai.configure(api_key=gemini_key)

# # -----------------------------
# # 3. Configure Pinecone 6.x
# # -----------------------------
# pinecone_key = os.getenv("PINECONE_API_KEY")
# pc = Pinecone(api_key=pinecone_key)

# INDEX_NAME = "jenkins-errors"

# # Create index if it doesn't exist
# if INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
#     pc.create_index(
#         name=INDEX_NAME,
#         dimension=1536,
#         metric="cosine",
#         spec=ServerlessSpec(cloud="aws", region="us-west-2")
#     )

# # Connect to index
# index = pc.Index(INDEX_NAME)

# # -----------------------------
# # 4. Local txt file
# # -----------------------------
# TXT_FILE = "jenkins_errors.txt"

# # -----------------------------
# # 5. Search in txt file
# # -----------------------------
# def search_txt_file(error_message):
#     if not os.path.exists(TXT_FILE):
#         return None
#     with open(TXT_FILE, "r", encoding="utf-8") as f:
#         content = f.read()
#     entries = content.split("ERROR:")
#     for entry in entries[1:]:
#         if error_message.lower() in entry.lower():
#             lines = entry.strip().split("\n")
#             solution_lines = [line for line in lines if line.startswith("SOLUTION:") or line.startswith("-")]
#             return "\n".join(solution_lines)
#     return None

# # -----------------------------
# # 6. Generate solution with Gemini 1.5 Flash Lite
# # -----------------------------
# def generate_solution_gemini(error_message):
#     model = genai.GenerativeModel("gemini-1.5-flash")
#     response = model.generate_content(
#         contents=error_message  # just pass contents; defaults are used
#     )
#     return response.text


# # -----------------------------
# # 7. Store solution in txt and Pinecone
# # -----------------------------
# def store_solution(error_message, solution):
#     # Append to txt
#     with open(TXT_FILE, "a", encoding="utf-8") as f:
#         f.write(f"\n\nERROR: {error_message}\nSOLUTION:\n- {solution.replace(chr(10), chr(10)+'- ')}")

#     # Convert solution to embedding vector using Gemini embeddings
#     vector = genai.embed_content(solution)  # returns list of floats

#     # Upsert to Pinecone
#     index.upsert(
#         vectors=[(error_message, vector, {"text": solution})]
#     )

# # -----------------------------
# # 8. Get solution (search or generate)
# # -----------------------------
# def get_solution(error_message):
#     solution = search_txt_file(error_message)
#     if solution:
#         print("Found solution in local txt file.")
#         return solution

#     print("Solution not found. Generating via Gemini 1.5 Flash...")
#     solution = generate_solution_gemini(error_message)
#     store_solution(error_message, solution)
#     return solution

# # -----------------------------
# # 9. Interactive Loop
# # -----------------------------
# if __name__ == "__main__":
#     print("=== Jenkins Error Resolver ===")
#     while True:
#         error_message = input("\nEnter Jenkins build error (or 'exit' to quit):\n")
#         if error_message.lower() in ["exit", "quit"]:
#             break
#         solution = get_solution(error_message)
#         print("\nSuggested Solution:\n", solution, "\n")


import os
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# -----------------------------
# 1. Load .env file
# -----------------------------
load_dotenv()

# -----------------------------
# 2. Configure Gemini AI
# -----------------------------
gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)

# -----------------------------
# 3. Configure Pinecone 6.x
# -----------------------------
pinecone_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_key)
INDEX_NAME = "jenkins-errors"

# Create index if it doesn't exist
if INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-west-2")
    )

# Connect to index
index = pc.Index(INDEX_NAME)

# -----------------------------
# 4. Search in Pinecone
# -----------------------------
def search_pinecone(error_message, threshold=0.8):
    query_vector = genai.embed_content(error_message)
    
    results = index.query(
        vector=query_vector,
        top_k=5,
        include_metadata=True
    )

    for match in results.matches:
        score = match.score  # cosine similarity
        if score >= threshold:
            return match.metadata["text"]
    return None

# -----------------------------
# 5. Generate solution with Gemini AI
# -----------------------------
def generate_solution_gemini(error_message):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        contents=error_message
    )
    return response.text

# -----------------------------
# 6. Store solution in Pinecone
# -----------------------------
def store_solution(error_message, solution):
    vector = genai.embed_content(solution) 
    index.upsert(
        vectors=[(error_message, vector, {"text": solution})]
    )

# -----------------------------
# 7. Get solution (search or generate)
# -----------------------------
def get_solution(error_message, threshold=0.8):
    solution = search_pinecone(error_message, threshold)
    if solution:
        print("Found similar solution in Pinecone DB.")
        return solution
    
    print("Solution not found or similarity too low. Generating via Gemini AI...")
    solution = generate_solution_gemini(error_message)
    store_solution(error_message, solution)
    return solution

# -----------------------------
# 8. Interactive Loop
# -----------------------------
if __name__ == "__main__":
    print("=== Jenkins Error Resolver ===")
    while True:
        error_message = input("\nEnter Jenkins build error (or 'exit' to quit):\n")
        if error_message.lower() in ["exit", "quit"]:
            break
        solution = get_solution(error_message, threshold=0.8)
        print("\nSuggested Solution:\n", solution, "\n")

