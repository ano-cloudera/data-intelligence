"""
CAI Job script: ingest satu PDF ke ChromaDB.

Dijalankan oleh CAI Job yang di-trigger via REST API dari backend.
Environment variables di-inject saat createJobRun:

  PDF_FILE_PATH     Path file PDF di dalam project filesystem CAI
                    (mis. /home/cdsw/rag_uploads/dokumen.pdf)
  COLLECTION_NAME   Nama ChromaDB collection (default: bank_jatim_knowledge)
  CHROMA_PERSIST_DIR Path ChromaDB (default: ./chroma_db)
  CHROMA_ENABLED    Set ke "true" (auto-set oleh script ini)

Cara register Job di CAI:
  Script: data-intelligence/ask-data/backend/ingest_pdf_job.py
  Runtime: Python 3
  Schedule: (tidak ada — on-demand via API)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("CHROMA_ENABLED", "true")

from app.core.config import get_settings
from app.services.rag_client import ChromaRagClient, RagClientError


def main() -> None:
    pdf_path = os.environ.get("PDF_FILE_PATH", "").strip()
    collection_name = os.environ.get("COLLECTION_NAME", "bank_jatim_knowledge").strip()

    if not pdf_path:
        print("[ERROR] PDF_FILE_PATH env var is required.", flush=True)
        sys.exit(1)

    if not Path(pdf_path).exists():
        print(f"[ERROR] File not found: {pdf_path}", flush=True)
        sys.exit(1)

    settings = get_settings()
    print(f"[INFO] PDF           : {pdf_path}", flush=True)
    print(f"[INFO] Collection    : {collection_name}", flush=True)
    print(f"[INFO] ChromaDB dir  : {Path(settings.chroma_persist_dir).resolve()}", flush=True)

    client = ChromaRagClient(settings=settings)

    try:
        n = client.ingest_pdf(collection_name=collection_name, pdf_path=pdf_path)
        print(f"[OK] Ingested {n} chunks from '{Path(pdf_path).name}' into '{collection_name}'.", flush=True)
    except RagClientError as exc:
        print(f"[ERROR] Ingest failed: {exc}", flush=True)
        sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] Unexpected error: {exc}", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
