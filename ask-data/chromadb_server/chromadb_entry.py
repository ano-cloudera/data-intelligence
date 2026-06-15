"""
CAI Application entry point for ChromaDB HTTP Server.

Setup di CAI:
  Name    : se-chromadb
  Script  : data-intelligence/ask-data/chromadb_server/chromadb_entry.py
  Resource: 1 vCPU / 2 GiB
  Allow Unauthenticated: Yes

Environment Variables:
  CHROMA_DATA_PATH   Path ke data directory
                     Default: /home/cdsw/data-intelligence/ask-data/chroma_db
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def resolve_port() -> int:
    raw = os.getenv("CDSW_APP_PORT") or os.getenv("PORT") or "8000"
    try:
        return int(raw)
    except ValueError:
        return 8000


def resolve_data_path() -> str:
    default = "/home/cdsw/data-intelligence/ask-data/chroma_db"
    path = os.getenv("CHROMA_DATA_PATH", default).strip()
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def ensure_chromadb() -> None:
    try:
        import chromadb  # noqa: F401
        logging.info("chromadb already installed: %s", chromadb.__version__)
    except ImportError:
        logging.info("Installing chromadb...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "chromadb>=0.4.0"],
            check=True,
        )


ensure_chromadb()

import chromadb

logging.info("chromadb version: %s", chromadb.__version__)

port = resolve_port()
data_path = resolve_data_path()

logging.info("ChromaDB HTTP Server starting")
logging.info("Port      : %s", port)
logging.info("Data path : %s", data_path)

# Use chromadb's own server directly via its internal API
# This works across chromadb versions 0.4.x - 0.6.x
try:
    # chromadb >= 0.5.x
    from chromadb.server.fastapi import FastAPI as ChromaFastAPI
    from chromadb.config import Settings as ChromaSettings

    settings = ChromaSettings(
        chroma_server_host="0.0.0.0",
        chroma_server_http_port=port,
        is_persistent=True,
        persist_directory=data_path,
        allow_reset=False,
        anonymized_telemetry=False,
    )
    server = ChromaFastAPI(settings)
    import uvicorn
    uvicorn.run(server.app(), host="0.0.0.0", port=port, log_level="info")

except Exception as e1:
    logging.warning("FastAPI server approach failed (%s), falling back to CLI", e1)

    # Fallback: run chromadb CLI and keep process alive
    cmd = [
        sys.executable, "-m", "chromadb.cli.cli", "run",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--path", data_path,
        "--log-path", "/dev/stdout",
    ]
    logging.info("Launching: %s", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)

    # Block until process ends, then exit with its code
    rc = proc.wait()
    logging.info("ChromaDB process exited with code %s", rc)
    # Do NOT raise SystemExit — let IPython session stay alive
    # If process exits, re-raise only on error
    if rc != 0:
        logging.error("ChromaDB exited with non-zero code: %s", rc)
