from pathlib import Path

import chromadb
import ollama
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).parent
DATABASE_DIR = BASE_DIR / "chroma_db"

CHAT_MODEL = "qwen3:1.7b"
EMBEDDING_MODEL = "nomic-embed-text"

app = FastAPI(
    title="AI Document Assistant API",
    description="Local RAG assistant using Ollama and ChromaDB",
    version="4.2"
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)


# Connect to the persistent vector database
client = chromadb.PersistentClient(
    path=str(DATABASE_DIR)
)


def get_embedding(text):
    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response["embeddings"][0]


@app.get("/")
def home():
    return {
        "message": "AI Document Assistant API is running"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(request: QuestionRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        collection = client.get_collection("documents")

        count = collection.count()

        if count == 0:
            raise HTTPException(
                status_code=503,
                detail="No indexed documents available."
            )

        # 1. Embed the question
        embedding = get_embedding(question)

        # 2. Retrieve relevant document sections
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(3, count),
            include=["documents", "metadatas", "distances"]
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        context_parts = []
        sources = []

        for document, metadata, distance in zip(
            documents, metadatas, distances
        ):
            context_parts.append(
                f"Source: {metadata['source']}, "
                f"Page: {metadata['page']}\n{document}"
            )

            sources.append({
                "document": metadata["source"],
                "page": metadata["page"],
                "distance": round(float(distance), 3)
            })

        context = "\n\n".join(context_parts)

        # 3. Generate answer with local Qwen3
        response = ollama.chat(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a document assistant. "
                        "Answer only using the provided context. "
                        "If the answer is not found, say so. "
                        "Do not invent facts. "
                        "Cite document names and pages."
                    )
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

        return {
            "question": question,
            "answer": response["message"]["content"],
            "sources": sources
        }

    except HTTPException:
        raise

    except Exception as error:
        print(f"RAG error: {error}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the question."
        ) from error
