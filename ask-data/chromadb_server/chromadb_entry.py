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

# ── Probe: find the right CLI entry point for this chromadb version ──────────
def probe_cli() -> list:
    """Try known CLI invocations and return the first one that shows 'run' in help."""
    candidates = [
        [sys.executable, "-m", "chromadb.cli.cli", "--help"],
        [sys.executable, "-m", "chromadb", "--help"],
        [sys.executable, "-c", "import chromadb.cli.cli; print('ok')"],
    ]
    for c in candidates:
        r = subprocess.run(c, capture_output=True, text=True)
        logging.info("Probe %s → rc=%s stdout=%s stderr=%s",
                     c[-1], r.returncode, r.stdout[:500], r.stderr[:500])

    # Also show chromadb package location and what modules exist
    r = subprocess.run(
        [sys.executable, "-c",
         "import chromadb, os; pkg=os.path.dirname(chromadb.__file__); "
         "[print(os.path.join(dp,f)) for dp,dn,fn in os.walk(pkg) for f in fn if f.endswith('.py') and 'cli' in f.lower()]"],
        capture_output=True, text=True,
    )
    logging.info("CLI-related files in chromadb package:\n%s", r.stdout)
    return []


probe_cli()

# ── Try to start chromadb server ─────────────────────────────────────────────
env = {**os.environ, "ANONYMIZED_TELEMETRY": "FALSE", "IS_PERSISTENT": "TRUE",
       "PERSIST_DIRECTORY": data_path, "CHROMA_SERVER_HOST": "0.0.0.0",
       "CHROMA_SERVER_HTTP_PORT": str(port)}

# Try different invocation styles for chromadb 1.5.x
run_cmds = [
    [sys.executable, "-m", "chromadb.cli.cli", "run", "--host", "0.0.0.0", "--port", str(port), "--path", data_path],
    [sys.executable, "-m", "chromadb", "run", "--host", "0.0.0.0", "--port", str(port), "--path", data_path],
    [sys.executable, "-m", "chromadb.cli", "run", "--host", "0.0.0.0", "--port", str(port), "--path", data_path],
]

working_cmd = None
for cmd in run_cmds:
    logging.info("Testing: %s", " ".join(cmd))
    r = subprocess.run(cmd + ["--help"] if "--help" not in cmd else cmd,
                       capture_output=True, text=True, timeout=10)
    logging.info("  rc=%s out=%s err=%s", r.returncode, r.stdout[:300], r.stderr[:300])
    # A 0 exit on --help means command is valid
    test_cmd = cmd[:-4] + ["--help"]  # replace path args with --help
    r2 = subprocess.run(
        [cmd[0], cmd[1], cmd[2], "--help"],
        capture_output=True, text=True, timeout=10,
    )
    if r2.returncode == 0 and ("run" in r2.stdout or "host" in r2.stdout):
        working_cmd = cmd
        logging.info("Found working CLI: %s", " ".join(cmd))
        break

if working_cmd is None:
    # Last resort: use chromadb Python API directly in a new process
    logging.warning("No working CLI found — using Python API in subprocess")
    api_script = f"""
import sys, os
os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'
import uvicorn
from chromadb.config import Settings
from chromadb.server.fastapi import FastAPI as ChromaFastAPI
settings = Settings(is_persistent=True, persist_directory='{data_path}', allow_reset=False, anonymized_telemetry=False)
server = ChromaFastAPI(settings)
uvicorn.run(server.app(), host='0.0.0.0', port={port}, log_level='info')
"""
    working_cmd = [sys.executable, "-c", api_script]

logging.info("Starting chromadb with: %s", " ".join(working_cmd[:4]))

proc = subprocess.Popen(working_cmd, stdout=sys.stdout, stderr=sys.stderr, env=env)
logging.info("ChromaDB PID: %s", proc.pid)

time.sleep(5)
if proc.poll() is not None:
    result = subprocess.run(working_cmd, capture_output=True, text=True, env=env, timeout=10)
    logging.error("ChromaDB died! STDOUT: %s", result.stdout[-2000:])
    logging.error("ChromaDB died! STDERR: %s", result.stderr[-2000:])
    raise RuntimeError(f"chromadb failed with code {result.returncode}")

logging.info("ChromaDB is running on port %s — keeping session alive", port)
while True:
    ret = proc.poll()
    if ret is not None:
        logging.error("ChromaDB exited (code %s) — restarting in 5s", ret)
        time.sleep(5)
        proc = subprocess.Popen(working_cmd, stdout=sys.stdout, stderr=sys.stderr, env=env)
        logging.info("ChromaDB restarted, PID: %s", proc.pid)
    time.sleep(2)
