from pathlib import Path

import pymupdf


CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def create_chunks(pdf_path):
    """Extract text from a PDF and split it into chunks."""

    pdf_path = Path(pdf_path)
    chunks = []

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text().strip()

            if not text:
                continue

            start = 0
            chunk_id = 1

            while start < len(text):
                end = start + CHUNK_SIZE
                chunk_text = text[start:end]

                chunks.append({
                    "source": pdf_path.name,
                    "page": page_number,
                    "chunk_id": chunk_id,
                    "text": chunk_text
                })

                if end >= len(text):
                    break

                start += CHUNK_SIZE - CHUNK_OVERLAP
                chunk_id += 1

    return chunks