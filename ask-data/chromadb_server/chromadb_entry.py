"""
CAI Application entry point for ChromaDB HTTP Server.
chromadb 1.5.x — runs chromadb CLI in a thread, keeps IPython session alive.

Setup di CAI:
  Name    : se-chromadb
  Script  : data-intelligence/ask-data/chromadb_server/chromadb_entry.py
  Resource: 1 vCPU / 2 GiB
  Allow Unauthenticated: Yes
"""

import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def resolve_port() -> int:
    raw = os.getenv("CDSW_APP_PORT") or os.getenv("PORT") or "9000"
    try:
        return int(raw)
    except ValueError:
        return 9000


def resolve_data_path() -> str:
    default = "/home/cdsw/data-intelligence/ask-data/chroma_db"
    path = os.getenv("CHROMA_DATA_PATH", default).strip()
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def ensure_chromadb() -> None:
    try:
        import chromadb  # noqa: F401
        logging.info("chromadb %s already installed", chromadb.__version__)
    except ImportError:
        logging.info("Installing chromadb...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "chromadb>=0.4.0"], check=True)


ensure_chromadb()

import chromadb

port = resolve_port()
data_path = resolve_data_path()

logging.info("chromadb version : %s", chromadb.__version__)
logging.info("Port      : %s", port)
logging.info("Data path : %s", data_path)

# Run chromadb CLI in a background thread so it owns its own event loop
# The main thread keeps running via a blocking loop — this keeps CAI session alive
cmd = [
    sys.executable, "-m", "chromadb.cli.cli", "run",
    "--host", "0.0.0.0",
    "--port", str(port),
    "--path", data_path,
    "--log-path", "/dev/stdout",
]
logging.info("Launching chromadb: %s", " ".join(cmd))

proc = subprocess.Popen(
    cmd,
    stdout=sys.stdout,
    stderr=sys.stderr,
    env={**os.environ, "ANONYMIZED_TELEMETRY": "FALSE"},
)

logging.info("ChromaDB server PID: %s", proc.pid)

# Keep the IPython session alive by polling the process
# If ChromaDB exits unexpectedly, log it and exit
while True:
    ret = proc.poll()
    if ret is not None:
        logging.error("ChromaDB process exited with code %s — restarting in 5s", ret)
        time.sleep(5)
        proc = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env={**os.environ, "ANONYMIZED_TELEMETRY": "FALSE"},
        )
        logging.info("ChromaDB restarted, new PID: %s", proc.pid)
    time.sleep(2)
