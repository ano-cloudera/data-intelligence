#!/usr/bin/env python3
"""
Ingest PDF documents into ChromaDB.
Run from ask-data/ directory:
    PYTHONPATH=backend .venv/bin/python scripts/ingest_documents.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import get_settings
from app.services.rag_client import ChromaRagClient, RagClientError

COLLECTION_NAME = "bankjatim_docs"
DOCUMENTS_DIR = Path(__file__).parent.parent / "data" / "documents"


def main() -> None:
    settings = get_settings()

    print(f"ChromaDB persist dir : {settings.chroma_persist_dir}")
    print(f"Embed model          : {settings.embed_model}")
    print(f"Ollama URL           : {settings.ollama_base_url}")
    print(f"Collection           : {COLLECTION_NAME}")
    print(f"Documents dir        : {DOCUMENTS_DIR}")
    print()

    pdfs = sorted(DOCUMENTS_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDF files found in documents dir.")
        sys.exit(1)

    client = ChromaRagClient(settings=settings)

    total_chunks = 0
    for pdf in pdfs:
        print(f"Ingesting: {pdf.name} ...", end=" ", flush=True)
        try:
            count = client.ingest_pdf(
                collection_name=COLLECTION_NAME,
                pdf_path=str(pdf),
            )
            print(f"{count} chunks")
            total_chunks += count
        except RagClientError as exc:
            print(f"FAILED: {exc}")

    print()
    print(f"Done. Total chunks ingested: {total_chunks}")
    print()

    collections = client.list_collections()
    for col in collections:
        print(f"Collection '{col['name']}': {col['document_count']} chunks")


if __name__ == "__main__":
    main()
