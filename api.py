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
    version="4.7"
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
    document: str | None = None

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
# Document list
# --------------------------------------------------

@app.get("/documents")
def list_documents():
    """Return all indexed PDF document names."""

    try:
        collection = client.get_collection("documents")

        # Retrieve metadata from ChromaDB
        results = collection.get(
            include=["metadatas"]
        )

        # Extract unique document names
        document_names = set()

        for metadata in results["metadatas"]:
            if metadata and "source" in metadata:
                document_names.add(metadata["source"])

        return {
            "documents": sorted(document_names),
            "count": len(document_names)
        }

    except chromadb.errors.NotFoundError:
        # No document collection exists yet
        return {
            "documents": [],
            "count": 0
        }

# --------------------------------------------------
# Delete PDF document
# --------------------------------------------------

@app.delete("/documents/{filename}")
def delete_document(filename: str):
    """Delete a PDF and its indexed chunks."""

    # 1. Validate filename
    if (
        not filename.lower().endswith(".pdf")
        or filename in (".", "..")
        or "/" in filename
        or "\\" in filename
        or filename != Path(filename).name
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF filename."
        )

    file_path = DOCUMENTS_DIR / filename

    # 2. Check that the PDF exists
    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="PDF file not found."
        )

    try:
        collection = client.get_collection("documents")

        # 3. Find indexed chunks belonging to this PDF
        results = collection.get(
            where={"source": filename},
            include=[]
        )

        chunk_ids = results["ids"]

        if not chunk_ids:
            raise HTTPException(
                status_code=404,
                detail="No indexed chunks found for this PDF."
            )

        # 4. Delete chunks from ChromaDB
        collection.delete(ids=chunk_ids)

        # 5. Delete the local PDF
        file_path.unlink()

        return {
            "message": "Document deleted successfully.",
            "filename": filename,
            "deleted_chunks": len(chunk_ids)
        }

    except HTTPException:
        raise

    except Exception as error:
        print(f"Delete error: {error}")

        raise HTTPException(
            status_code=500,
            detail="Could not delete the document."
        ) from error

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
        
        # Optional: restrict search to one PDF
        selected_document = request.document

        query_options = {
            "query_embeddings": [embedding],
            "n_results": min(5, count),
            "include": [
                "documents",
                "metadatas",
                "distances"
            ]
        }

        if selected_document:
            matching_chunks = collection.get(
                where={"source": selected_document},
                include=[]
            )

            matching_count = len(matching_chunks["ids"])

            if matching_count == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Selected document was not found."
                )

            query_options["where"] = {
                "source": selected_document
            }
            query_options["n_results"] = min(
                5,
                matching_count
            )

        results = collection.query(**query_options)

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        
        context_parts = []
        sources = []

        for number, (document, metadata, distance) in enumerate(
            zip(documents, metadatas, distances),
            start=1
        ):
            context_parts.append(
                f"[{number}] Source: {metadata['source']}, "
                f"Page: {metadata['page']}\n"
                f"{document}"
            )

            sources.append({
                "number": number,
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
    			"You are a precise document assistant. "
    			"Answer questions using only the provided document context. "
    			"Do not use outside knowledge or invent facts. "
    			"Each context passage has a source number such as [1] or [2]. "
    			"Cite the relevant source numbers directly in your answer. "
    			"Use citations like [1] or [2] after factual statements. "
    			"Only cite source numbers that appear in the context. "
    			"If the context does not contain enough information, "
    			"clearly say that the answer cannot be found in the documents. "
    			"Keep answers clear, accurate and concise."
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
