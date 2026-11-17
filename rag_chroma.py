from pathlib import Path

import chromadb
import ollama

BASE_DIR = Path(__file__).parent
DATABASE_DIR = BASE_DIR / "chroma_db"

CHAT_MODEL = "qwen3:1.7b"
EMBEDDING_MODEL = "nomic-embed-text"
COLLECTION_NAME = "documents"


def get_embedding(text):
    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response["embeddings"][0]


# Connect to persistent ChromaDB
client = chromadb.PersistentClient(
    path=str(DATABASE_DIR)
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

print(f"Loaded {collection.count()} stored chunks.")
print("RAG Assistant with ChromaDB is ready.")
print("Type 'exit' to quit.")


while True:
    question = input("\nYour question: ").strip()

    if question.lower() == "exit":
        break

    if not question:
        continue

    # Embed only the user's question
    question_embedding = get_embedding(question)

    # Search stored embeddings
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(3, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # Build context for Qwen3
    context_parts = []

    for document, metadata in zip(documents, metadatas):
        context_parts.append(
            f"Source: {metadata['source']}, "
            f"Page: {metadata['page']}\n"
            f"{document}"
        )

    context = "\n\n".join(context_parts)

    system_prompt = """
You are a document assistant.

Answer the user's question using only the
provided document context.

If the answer is not found in the context,
clearly state that the information is unavailable.

Do not invent information.

Mention document names and page numbers
when answering.
"""

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
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

    for metadata, distance in zip(metadatas, distances):
        print(
            f"- {metadata['source']}, "
            f"page {metadata['page']} "
            f"(distance: {distance:.3f})"
        )
