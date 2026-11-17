from pathlib import Path
import pymupdf
import json

DOCUMENTS_DIR = Path(__file__).parent / "documents"
OUTPUT_FILE = Path(__file__).parent / "chunks.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def split_text(text, size=500, overlap=100):
    """Split text into overlapping chunks."""

    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Invalid chunk settings")

    chunks = []
    step = size - overlap

    for start in range(0, len(text), step):
        chunk = text[start:start + size].strip()

        if chunk:
            chunks.append(chunk)

        if start + size >= len(text):
            break

    return chunks


all_chunks = []

for pdf_path in sorted(DOCUMENTS_DIR.glob("*.pdf")):
    print(f"Processing: {pdf_path.name}")

    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text(sort=True)

            page_chunks = split_text(
                text,
                CHUNK_SIZE,
                CHUNK_OVERLAP
            )

            for chunk_number, chunk in enumerate(page_chunks, start=1):
                all_chunks.append({
                    "source": pdf_path.name,
                    "page": page_number,
                    "chunk_id": chunk_number,
                    "text": chunk
                })

print(f"\nTotal chunks created: {len(all_chunks)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(
        all_chunks,
        file,
        ensure_ascii=False,
        indent=2
    )

print(f"Saved to: {OUTPUT_FILE}")
