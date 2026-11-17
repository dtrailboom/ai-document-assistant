from pathlib import Path
import pymupdf

DOCUMENTS_DIR = Path(__file__).parent / "documents"

pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))

if not pdf_files:
    print("No PDF files found.")
else:
    for pdf_path in pdf_files:
        print(f"\nReading: {pdf_path.name}")

        with pymupdf.open(pdf_path) as document:
            for page_number, page in enumerate(document, start=1):
                text = page.get_text()

                print(f"\n--- Page {page_number} ---")
                print(text[:1000])
