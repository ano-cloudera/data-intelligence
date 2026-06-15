"""
CAI Application entry point for ChromaDB HTTP Server.

Setup di CAI:
  Name    : bjt-chromadb
  Script  : data-intelligence/ask-data/chromadb_server/chromadb_entry.py
  Resource: 1 vCPU / 2 GiB
  Allow Unauthenticated: Yes

Environment Variables:
  CHROMA_DATA_PATH   Path ke data directory (default: existing chroma_db)
                     Set ke: /home/cdsw/data-intelligence/ask-data/chroma_db
                     supaya data existing langsung terbaca tanpa re-ingest.

Migrasi dari local ChromaDB:
  Tidak perlu copy data — ChromaDB App ini langsung point ke
  /home/cdsw/data-intelligence/ask-data/chroma_db/ yang sudah berisi
  data hasil ingest sebelumnya.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def resolve_port() -> str:
    return os.getenv("CDSW_APP_PORT") or os.getenv("PORT") or "8000"

def resolve_data_path() -> str:
    # Default: point ke existing chroma_db di project filesystem
    default = "/home/cdsw/data-intelligence/ask-data/chroma_db"
    path = os.getenv("CHROMA_DATA_PATH", default).strip()
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

def ensure_chromadb() -> None:
    try:
        import chromadb  # noqa: F401
        logging.info("chromadb already installed.")
    except ImportError:
        logging.info("Installing chromadb...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "chromadb>=0.6.0"],
            check=True,
        )

def main() -> None:
    port = resolve_port()
    data_path = resolve_data_path()

    logging.info("ChromaDB HTTP Server starting")
    logging.info("Port      : %s", port)
    logging.info("Data path : %s", data_path)

    ensure_chromadb()

    cmd = [
        sys.executable, "-m", "chromadb.cli.cli", "run",
        "--host", "0.0.0.0",
        "--port", port,
        "--path", data_path,
        "--log-path", "/dev/stdout",
    ]

    logging.info("Launching: %s", " ".join(cmd))
    process = subprocess.Popen(cmd)
    process.wait()
    raise SystemExit(process.returncode)

if __name__ == "__main__":
    main()
