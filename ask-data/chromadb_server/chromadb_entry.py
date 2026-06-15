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
import time
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


def ensure_deps() -> None:
    pkgs = [
        "chromadb>=0.6.0",
        "uvicorn[standard]>=0.29.0",
        "opentelemetry-api",
        "opentelemetry-sdk",
        "opentelemetry-instrumentation-fastapi",
    ]
    missing = []
    try:
        import chromadb  # noqa: F401
    except ImportError:
        missing.append("chromadb>=0.6.0")
    try:
        import uvicorn  # noqa: F401
    except ImportError:
        missing.append("uvicorn[standard]>=0.29.0")
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # noqa: F401
    except ImportError:
        missing.extend([
            "opentelemetry-api",
            "opentelemetry-sdk",
            "opentelemetry-instrumentation-fastapi",
        ])

    if missing:
        logging.info("Installing missing deps: %s", missing)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q"] + missing,
            check=True,
        )
    else:
        logging.info("All dependencies already installed.")


ensure_deps()

import chromadb
import uvicorn
from chromadb.app import create_app
from chromadb.config import Settings as ChromaSettings

port = resolve_port()
data_path = resolve_data_path()

logging.info("ChromaDB HTTP Server starting")
logging.info("Port      : %s", port)
logging.info("Data path : %s", data_path)

chroma_settings = ChromaSettings(
    is_persistent=True,
    persist_directory=data_path,
    allow_reset=False,
    anonymized_telemetry=False,
)

server_app = create_app(chroma_settings)

uvicorn.run(
    server_app,
    host="0.0.0.0",
    port=port,
    log_level="info",
)
