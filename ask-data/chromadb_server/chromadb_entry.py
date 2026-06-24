"""
CAI Application entry point for ChromaDB HTTP Server.
chromadb 1.5.x

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
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def resolve_port() -> int:
    for var in ["CDSW_APP_PORT", "PORT", "CDSW_PUBLIC_PORT"]:
        logging.info("ENV %s = %s", var, os.getenv(var, "(not set)"))
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

# Run a quick test to see what error the subprocess gets
logging.info("=== TESTING subprocess error ===")
test_script = f"""
import sys, os, traceback
os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'
try:
    import uvicorn
    from chromadb.config import Settings
    from chromadb.server.fastapi import FastAPI as ChromaFastAPI
    settings = Settings(is_persistent=True, persist_directory='{data_path}', allow_reset=False, anonymized_telemetry=False)
    print("Settings OK", flush=True)
    server = ChromaFastAPI(settings)
    print("ChromaFastAPI OK", flush=True)
    app = server.app()
    print("app() OK", flush=True)
    # Don't actually run uvicorn — just check imports
    print("ALL OK", flush=True)
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
"""
result = subprocess.run([sys.executable, "-c", test_script], capture_output=True, text=True, timeout=30)
logging.info("Test STDOUT: %s", result.stdout)
logging.info("Test STDERR: %s", result.stderr)
logging.info("Test rc: %s", result.returncode)

if result.returncode != 0:
    logging.error("Subprocess cannot import chromadb server — see error above")
    # Try installing missing deps
    logging.info("Installing opentelemetry deps...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                    "opentelemetry-api", "opentelemetry-sdk",
                    "opentelemetry-instrumentation-fastapi",
                    "uvicorn[standard]"], check=False)
    # Retry test
    result2 = subprocess.run([sys.executable, "-c", test_script], capture_output=True, text=True, timeout=30)
    logging.info("Retry STDOUT: %s", result2.stdout)
    logging.info("Retry STDERR: %s", result2.stderr)

logging.info("=== STARTING SERVER ===")

api_script = f"""
import sys, os
os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'
os.environ['IS_PERSISTENT'] = 'TRUE'
os.environ['PERSIST_DIRECTORY'] = '{data_path}'
os.environ['ALLOW_RESET'] = 'FALSE'
os.environ['CHROMA_SERVER_HTTP_PORT'] = '{port}'
os.environ['CHROMA_SERVER_HOST'] = '0.0.0.0'

import uvicorn
from chromadb.config import Settings, System
from chromadb.server.fastapi import FastAPI as ChromaFastAPI

settings = Settings(
    is_persistent=True,
    persist_directory='{data_path}',
    allow_reset=False,
    anonymized_telemetry=False,
    chroma_server_http_port={port},
    chroma_server_host='0.0.0.0',
)

# Instantiate but do NOT call .run() — extract the ASGI app only
server = ChromaFastAPI(settings)
asgi_app = server.app()

uvicorn.run(asgi_app, host='0.0.0.0', port={port}, log_level='info')
"""

env = {**os.environ, "ANONYMIZED_TELEMETRY": "FALSE"}


def start_proc():
    # Pipe stderr so we can capture it on crash
    return subprocess.Popen(
        [sys.executable, "-c", api_script],
        stdout=sys.stdout,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )


proc = start_proc()
logging.info("ChromaDB PID: %s", proc.pid)

# Give it time to start
time.sleep(5)

if proc.poll() is not None:
    stderr_out = proc.stderr.read() if proc.stderr else ""
    logging.error("ChromaDB died immediately! STDERR:\n%s", stderr_out)
    raise RuntimeError(f"chromadb failed with code {proc.returncode}")

logging.info("ChromaDB is running on port %s", port)

while True:
    ret = proc.poll()
    if ret is not None:
        stderr_out = proc.stderr.read() if proc.stderr else ""
        logging.error("ChromaDB exited (code %s). STDERR:\n%s", ret, stderr_out)
        logging.info("Restarting in 5s...")
        time.sleep(5)
        proc = start_proc()
        logging.info("ChromaDB restarted, PID: %s", proc.pid)
    time.sleep(2)
