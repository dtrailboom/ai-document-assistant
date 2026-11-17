import json
from pathlib import Path

import chromadb
import ollama
from chromadb.errors import NotFoundError

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


# 1. Load document chunks
with open(CHUNKS_FILE, encoding="utf-8") as file:
    chunks = json.load(file)

if not chunks:
    raise SystemExit("No chunks found. Run chunk_documents.py first.")

print(f"Loaded {len(chunks)} chunks.")


# 2. Connect to local database
client = chromadb.PersistentClient(path=str(DATABASE_DIR))

# Rebuild the collection for a clean index
try:
    client.delete_collection(COLLECTION_NAME)
except NotFoundError:
    pass

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


# 3. Create embeddings and store chunks
for index, chunk in enumerate(chunks, start=1):
    text = chunk["text"]

    embedding = get_embedding(text)

    document_id = (
        f"{chunk['source']}_"
        f"page{chunk['page']}_"
        f"chunk{chunk['chunk_id']}"
    )

    collection.add(
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
print(f"Database location: {DATABASE_DIR}")
