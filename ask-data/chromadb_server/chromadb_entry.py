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
# First, check what CLI options are available in this chromadb version
probe = subprocess.run(
    [sys.executable, "-m", "chromadb.cli.cli", "run", "--help"],
    capture_output=True, text=True,
)
logging.info("chromadb CLI help:\n%s\n%s", probe.stdout, probe.stderr)

# Build command — omit --log-path which may not exist in 1.5.x
cmd = [
    sys.executable, "-m", "chromadb.cli.cli", "run",
    "--host", "0.0.0.0",
    "--port", str(port),
    "--path", data_path,
]

# Add --log-path only if supported
if "--log-path" in probe.stdout:
    cmd += ["--log-path", "/dev/stdout"]

logging.info("Launching: %s", " ".join(cmd))

env = {**os.environ, "ANONYMIZED_TELEMETRY": "FALSE", "CHROMA_LOG_CONFIG": ""}


def start_proc():
    return subprocess.Popen(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=env,
    )


proc = start_proc()
logging.info("ChromaDB server PID: %s", proc.pid)

# Give it a moment to start, then check if it died immediately
time.sleep(3)
if proc.poll() is not None:
    # Died immediately — re-run with output captured to see the error
    logging.error("ChromaDB died immediately — capturing output for debug")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    logging.error("STDOUT: %s", result.stdout[-3000:] if result.stdout else "(empty)")
    logging.error("STDERR: %s", result.stderr[-3000:] if result.stderr else "(empty)")
    logging.error("Exit code: %s", result.returncode)
    raise RuntimeError(f"chromadb CLI failed with code {result.returncode}")

logging.info("ChromaDB is running — keeping session alive")
while True:
    ret = proc.poll()
    if ret is not None:
        logging.error("ChromaDB exited with code %s", ret)
        logging.info("Restarting in 5s...")
        time.sleep(5)
        proc = start_proc()
        logging.info("ChromaDB restarted, PID: %s", proc.pid)
    time.sleep(2)
