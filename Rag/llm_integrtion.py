from google import genai
from rag import search, embeddings, final_chunks

from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def generate(query, search_results):
    context = ""
    for i, (chunk, score) in enumerate(search_results):
        context += f"Source {i+1} ({chunk['team1']} vs {chunk['team2']}, {chunk['season']}):\n{chunk['content']}\n\n"

    prompt = f"""You are an IPL cricket analyst. Answer the question using ONLY the information in the sources below. Do not use any outside knowledge. If the sources don't contain enough information to answer, say so clearly instead of guessing.

SOURCES:
{context}

QUESTION: {query}

ANSWER:"""

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config={"temperature": 0}
    )

    return response.text


if __name__ == "__main__":
    query = input("Enter your query: ")
    results = search(query, embeddings, final_chunks, top_k=5)
    answer = generate(query, results)
    print("\n--- ANSWER ---")
    print(answer)