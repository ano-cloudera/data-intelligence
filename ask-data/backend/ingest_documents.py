"""
Ingest all PDF documents into ChromaDB collection 'bank_jatim_knowledge'.

Run this once from ask-data/backend/ before using the Knowledge Base feature:

    cd ask-data/backend
    python ingest_documents.py

The script reads PDFs from ../data/documents/, ingests them into ChromaDB,
and copies them into ./rag_pdfs/ so the /rag/documents/ endpoint can serve them.

No environment variables required — chromadb and sentence-transformers are used
automatically if ollama is not available.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running from backend/ without pip install -e
sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("CHROMA_ENABLED", "true")

from app.core.config import get_settings          # noqa: E402
from app.services.rag_client import ChromaRagClient  # noqa: E402

COLLECTION_NAME = "bank_jatim_knowledge"
DOCS_DIR = Path(__file__).parent.parent / "data" / "documents"


def main() -> None:
    settings = get_settings()
    client = ChromaRagClient(settings=settings)

    pdf_files = sorted(DOCS_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"[ERROR] No PDF files found in: {DOCS_DIR}")
        sys.exit(1)

    print(f"ChromaDB dir : {Path(settings.chroma_persist_dir).resolve()}")
    print(f"PDF serve dir: {Path(settings.rag_pdf_dir).resolve()}")
    print(f"Collection   : {COLLECTION_NAME}")
    print(f"Documents    : {len(pdf_files)} file(s)")
    print()

    total = 0
    for pdf in pdf_files:
        print(f"  [{pdf.name}] ... ", end="", flush=True)
        try:
            n = client.ingest_pdf(collection_name=COLLECTION_NAME, pdf_path=str(pdf))
            total += n
            print(f"{n} chunks")
        except Exception as exc:
            print(f"FAILED — {exc}")

    print()
    print(f"Done. {total} total chunks in '{COLLECTION_NAME}'.")
    print()
    print("Next: in the app → Settings → Knowledge Base")
    print(f"  • Enable toggle")
    print(f"  • Select collection: {COLLECTION_NAME}")
    print(f"  • Click Save Knowledge Base")
    print()
    print("Test questions:")
    print("  ID: Apa strategi retensi untuk nasabah dormant risiko tinggi?")
    print("  ID: Bagaimana prinsip governance customer analytics di Bank Jawa Timur?")
    print("  ID: Apa panduan next best action untuk campaign reactivation?")
    print("  EN: What is the dormant customer retention strategy?")
    print("  EN: How should campaigns be planned based on segment and risk level?")


if __name__ == "__main__":
    main()
