import json
import math
from pathlib import Path

import ollama

BASE_DIR = Path(__file__).parent
CHUNKS_FILE = BASE_DIR / "chunks.json"

CHAT_MODEL = "qwen3:1.7b"
EMBEDDING_MODEL = "nomic-embed-text"


def get_embedding(text):
    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response["embeddings"][0]


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


with open(CHUNKS_FILE, encoding="utf-8") as file:
    chunks = json.load(file)

print(f"Loaded {len(chunks)} document chunks.")

print("Creating embeddings...")
for chunk in chunks:
    chunk["embedding"] = get_embedding(chunk["text"])

print("RAG Assistant ready. Type 'exit' to quit.")

while True:
    question = input("\nYour question: ").strip()

    if question.lower() == "exit":
        break

    if not question:
        continue

    question_embedding = get_embedding(question)

    for chunk in chunks:
        chunk["score"] = cosine_similarity(
            question_embedding,
            chunk["embedding"]
        )

    top_chunks = sorted(
        chunks,
        key=lambda item: item["score"],
        reverse=True
    )[:3]

    context = "\n\n".join(
        f"[Source: {chunk['source']}, page {chunk['page']}]\n"
        f"{chunk['text']}"
        for chunk in top_chunks
    )

    system_prompt = """
You are a document assistant.

Answer the user's question using only the provided
document context.

If the answer is not in the documents, say that
the information was not found.

Do not invent facts.

Mention the document and page when possible.
"""

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Document context:\n{context}\n\n"
                    f"Question: {question}"
                )
            }
        ],
        think=False
    )

    print("\nAssistant:")
    print(response["message"]["content"])

    print("\nRetrieved sources:")
    for chunk in top_chunks:
        print(
            f"- {chunk['source']}, page {chunk['page']} "
            f"(similarity: {chunk['score']:.3f})"
        )
