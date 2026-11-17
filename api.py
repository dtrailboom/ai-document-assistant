from pathlib import Path

import chromadb
import ollama
import pymupdf

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pdf_service import create_chunks
from index_documents import index_chunks


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).parent
DATABASE_DIR = BASE_DIR / "chroma_db"
DOCUMENTS_DIR = BASE_DIR / "documents"

CHAT_MODEL = "qwen3:1.7b"
EMBEDDING_MODEL = "nomic-embed-text"

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="AI Document Assistant API",
    description="Local RAG assistant using Ollama and ChromaDB",
    version="4.4"
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)


# --------------------------------------------------
# Request models
# --------------------------------------------------

class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)


# --------------------------------------------------
# ChromaDB connection
# --------------------------------------------------

client = chromadb.PersistentClient(
    path=str(DATABASE_DIR)
)


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def get_embedding(text: str):
    """Generate an embedding using the local Ollama model."""

    response = ollama.embed(
        model=EMBEDDING_MODEL,
        input=text
    )

    return response["embeddings"][0]


# --------------------------------------------------
# Web interface
# --------------------------------------------------

@app.get("/")
def home():
    """Display the web interface."""

    return FileResponse(
        BASE_DIR / "static" / "index.html"
    )


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
def health():
    """Check whether the API is running."""

    return {"status": "ok"}


# --------------------------------------------------
# RAG question answering
# --------------------------------------------------

@app.post("/ask")
def ask(request: QuestionRequest):
    """Answer questions using indexed PDF documents."""

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

        # 1. Generate embedding for the question
        embedding = get_embedding(question)

        # 2. Retrieve relevant document chunks
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(3, count),
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        context_parts = []
        sources = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):
            context_parts.append(
                f"Source: {metadata['source']}, "
                f"Page: {metadata['page']}\n"
                f"{document}"
            )

            sources.append({
                "document": metadata["source"],
                "page": metadata["page"],
                "distance": round(float(distance), 3)
            })

        context = "\n\n".join(context_parts)

        # 3. Generate an answer using local Qwen3
        response = ollama.chat(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a document assistant. "
                        "Answer only using the provided context. "
                        "If the answer is not found in the "
                        "context, say so. "
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
            detail=(
                "An error occurred while "
                "processing the question."
            )
        ) from error


# --------------------------------------------------
# PDF upload
# --------------------------------------------------

@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF document.

    - Accept PDF files only
    - Maximum size: 10 MB
    - Prevent overwriting existing files
    - Validate PDF content
    - Store documents locally

    PDF documents are automatically indexed in ChromaDB.
    """

    # 1. Check file extension
    if (
        not file.filename
        or not file.filename.lower().endswith(".pdf")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    # 2. Create documents directory
    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 3. Sanitize filename
    filename = Path(
        file.filename.replace("\\", "/")
    ).name

    if filename in ("", ".", ".."):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )

    file_path = DOCUMENTS_DIR / filename

    # 4. Prevent overwriting existing files
    if file_path.exists():
        raise HTTPException(
            status_code=409,
            detail=(
                "A document with this filename "
                "already exists."
            )
        )

    total_size = 0
    created_file = False

    try:
        # 5. Save PDF in chunks
        with open(file_path, "xb") as output:
            created_file = True

            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="PDF exceeds the 10 MB limit."
                    )

                output.write(chunk)

        # 6. Validate PDF signature
        with open(file_path, "rb") as saved_file:
            signature = saved_file.read(5)

        if signature != b"%PDF-":
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file signature."
            )

        # 7. Verify that PyMuPDF can open the PDF
        try:
            with pymupdf.open(file_path) as document:
                page_count = len(document)

                if page_count == 0:
                    raise ValueError(
                        "PDF contains no pages."
                    )

        except Exception as error:
            raise HTTPException(
                status_code=400,
                detail="PDF is invalid or cannot be read."
            ) from error

        
        # 8. Extract text and create chunks
        chunks = create_chunks(file_path)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="PDF contains no extractable text."
            )

        # 9. Generate embeddings and index chunks
        indexed_count = index_chunks(chunks)

        # 10. Return successful response
        return {
            "message": "PDF uploaded and indexed successfully.",
            "filename": filename,
            "size_bytes": total_size,
            "pages": page_count,
            "chunks": indexed_count,
            "indexed": True
        }

    except Exception:
        # Remove incomplete or invalid uploads
        if created_file:
            file_path.unlink(missing_ok=True)

        raise

    finally:
        file.file.close()
