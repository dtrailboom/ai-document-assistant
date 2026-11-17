import json
from pathlib import Path

import chromadb
import ollama


BASE_DIR = Path(__file__).parent
CHUNKS_FILE = BASE_DIR / "chunks.json"
DATABASE_DIR = BASE_DIR / "chroma_db"

EMBEDDING_MODEL = "nomic-embed-text"
COLLECTION_NAME = "documents"


def get_embedding(text):
    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response["embeddings"][0]


def index_chunks(chunks):
    """Add document chunks to ChromaDB."""

    client = chromadb.PersistentClient(
        path=str(DATABASE_DIR)
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    for index, chunk in enumerate(chunks, start=1):
        text = chunk["text"]

        embedding = get_embedding(text)

        document_id = (
            f"{chunk['source']}_"
            f"page{chunk['page']}_"
            f"chunk{chunk['chunk_id']}"
        )

        collection.upsert(
            ids=[document_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[{
                "source": chunk["source"],
                "page": chunk["page"],
                "chunk_id": chunk["chunk_id"]
            }]
        )

        print(f"Indexed {index}/{len(chunks)}")

    print("\nIndexing complete!")
    print(f"Documents stored: {collection.count()}")

    return len(chunks)


def main():
    """Index chunks stored in chunks.json."""

    with open(CHUNKS_FILE, encoding="utf-8") as file:
        chunks = json.load(file)

    if not chunks:
        print("No chunks found.")
        return

    print(f"Loaded {len(chunks)} chunks.")

    index_chunks(chunks)


if __name__ == "__main__":
    main()