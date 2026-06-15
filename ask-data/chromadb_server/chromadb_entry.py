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
import socket
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
    pkgs_needed = []
    try:
        import chromadb  # noqa: F401
    except ImportError:
        pkgs_needed.append("chromadb>=0.4.0")
    try:
        import nest_asyncio  # noqa: F401
    except ImportError:
        pkgs_needed.append("nest-asyncio")
    try:
        import uvicorn  # noqa: F401
    except ImportError:
        pkgs_needed.append("uvicorn[standard]")

    if pkgs_needed:
        logging.info("Installing: %s", pkgs_needed)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q"] + pkgs_needed,
            check=True,
        )
    else:
        logging.info("All dependencies already installed.")


def free_port(port: int) -> None:
    """Kill any process holding the port."""
    freed = False
    try:
        result = subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
        if result.returncode == 0:
            freed = True
    except FileNotFoundError:
        pass

    if not freed:
        try:
            out = subprocess.check_output(["lsof", "-ti", f"tcp:{port}"], text=True).strip()
            for pid in out.splitlines():
                subprocess.run(["kill", "-9", pid.strip()], check=False)
            if out:
                freed = True
        except Exception:
            pass

    if freed:
        logging.info("Freed port %s", port)
        time.sleep(1)


ensure_deps()

import asyncio
import chromadb
import nest_asyncio
import uvicorn
from chromadb.config import Settings as ChromaSettings
from chromadb.server.fastapi import FastAPI as ChromaFastAPI

nest_asyncio.apply()

port = resolve_port()
data_path = resolve_data_path()

free_port(port)

logging.info("chromadb version : %s", chromadb.__version__)
logging.info("ChromaDB HTTP Server starting")
logging.info("Port      : %s", port)
logging.info("Data path : %s", data_path)

# chromadb 1.5.x: do NOT pass chroma_server_host/port in Settings
# — that causes ChromaFastAPI to bind the port internally before uvicorn does.
# Only set persistence settings; let uvicorn own the port binding.
settings = ChromaSettings(
    is_persistent=True,
    persist_directory=data_path,
    allow_reset=False,
    anonymized_telemetry=False,
)

server = ChromaFastAPI(settings)

# Pre-bind the socket with SO_REUSEADDR so restart doesn't fail
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("0.0.0.0", port))
sock.set_inheritable(True)

logging.info("Socket bound to port %s — starting uvicorn", port)

config = uvicorn.Config(
    app=server.app(),
    log_level="info",
)
uv_server = uvicorn.Server(config)

loop = asyncio.get_event_loop()
loop.run_until_complete(uv_server.serve(sockets=[sock]))
