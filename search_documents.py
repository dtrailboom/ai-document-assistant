import json
import math
from pathlib import Path
import ollama

BASE_DIR = Path(__file__).parent
CHUNKS_FILE = BASE_DIR / "chunks.json"
EMBEDDING_MODEL = "nomic-embed-text"


def cosine_similarity(a, b):
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def get_embedding(text):
    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response["embeddings"][0]


with open(CHUNKS_FILE, encoding="utf-8") as file:
    chunks = json.load(file)

print(f"Loaded {len(chunks)} chunks.")

print("Creating embeddings...")
for index, chunk in enumerate(chunks, start=1):
    chunk["embedding"] = get_embedding(chunk["text"])
    print(f"Embedded {index}/{len(chunks)}")

question = input("\nAsk a question about your documents: ")

question_embedding = get_embedding(question)

for chunk in chunks:
    chunk["score"] = cosine_similarity(
        question_embedding,
        chunk["embedding"]
    )

results = sorted(
    chunks,
    key=lambda item: item["score"],
    reverse=True
)[:3]

print("\nMost relevant document sections:\n")

for result in results:
    print(f"Source: {result['source']}")
    print(f"Page: {result['page']}")
    print(f"Similarity: {result['score']:.3f}")
    print(result["text"])
    print("-" * 50)
