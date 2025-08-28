import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import ContentType
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_key)


#Creating DB

pinecone_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_key)

INDEX_NAME = "error-store"

# Create index if it doesn't exist
if INDEX_NAME not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=3072,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

# Connect to index
index = pc.Index(INDEX_NAME)

with open("jenkins_errors.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Split into chunks
def chunk_text(text, chunk_size=200):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

chunks = chunk_text(text)
print(chunks.__sizeof__())

models = list(genai.list_models())
# for model in models:
#     print(model)

# for i, chunk in enumerate(chunks):
#     embedding_vector = genai.embed_content(model="models/gemini-embedding-001", content=chunk)
#     index.upsert([(str(i), embedding_vector, {"text": chunk})])
def embed_query(query):
    response = genai.embed_content(model="models/gemini-embedding-001", content=query)
    return response["embedding"] if isinstance(response, dict) else response

# print("Chunks stored successfully!")

for i, chunk in enumerate(chunks):
    embedding_response = genai.embed_content(model="models/gemini-embedding-001", content=chunk)
    embedding_vector = embedding_response["embedding"] if isinstance(embedding_response, dict) else embedding_response
    index.upsert([(str(i), embedding_vector, {"text": chunk})])

print("Chunks stored successfully!")

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

if __name__ == "__main__":
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