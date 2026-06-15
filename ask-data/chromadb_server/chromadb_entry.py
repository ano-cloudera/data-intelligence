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


def force_free_port(port: int) -> None:
    """Aggressively free a port using multiple methods."""
    logging.info("Attempting to free port %s...", port)

    # Method 1: fuser -k
    try:
        subprocess.run(["fuser", "-k", "-9", f"{port}/tcp"], capture_output=True)
    except FileNotFoundError:
        pass

    # Method 2: lsof + kill -9
    try:
        out = subprocess.check_output(
            ["lsof", "-ti", f"tcp:{port}"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        for pid in out.splitlines():
            pid = pid.strip()
            if pid:
                logging.info("Killing PID %s on port %s", pid, port)
                subprocess.run(["kill", "-9", pid], check=False)
    except Exception:
        pass

    # Method 3: /proc/net/tcp — find and kill without external tools
    try:
        hex_port = format(port, "04X")
        with open("/proc/net/tcp") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 10:
                    continue
                local = parts[1]
                lport = int(local.split(":")[1], 16)
                if lport == port:
                    inode = parts[9]
                    # Find PID owning this inode
                    result = subprocess.run(
                        ["grep", "-r", f"socket:[{inode}]", "/proc/*/fd"],
                        capture_output=True, text=True
                    )
                    for match in result.stdout.splitlines():
                        pid = match.split("/")[2]
                        if pid.isdigit():
                            logging.info("Killing PID %s (inode %s) on port %s", pid, inode, port)
                            subprocess.run(["kill", "-9", pid], check=False)
    except Exception:
        pass

    # Wait for OS to release the port
    for i in range(10):
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_sock.bind(("0.0.0.0", port))
            test_sock.close()
            logging.info("Port %s is free after %s attempts", port, i + 1)
            return
        except OSError:
            logging.info("Port %s still busy, waiting... (%s/10)", port, i + 1)
            time.sleep(1)

    logging.warning("Could not free port %s after 10 attempts, proceeding anyway", port)


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

force_free_port(port)

logging.info("chromadb version : %s", chromadb.__version__)
logging.info("ChromaDB HTTP Server starting")
logging.info("Port      : %s", port)
logging.info("Data path : %s", data_path)

settings = ChromaSettings(
    is_persistent=True,
    persist_directory=data_path,
    allow_reset=False,
    anonymized_telemetry=False,
)

server = ChromaFastAPI(settings)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
sock.bind(("0.0.0.0", port))
sock.set_inheritable(True)

logging.info("Socket bound — starting uvicorn on port %s", port)

config = uvicorn.Config(app=server.app(), log_level="info")
uv_server = uvicorn.Server(config)

loop = asyncio.get_event_loop()
loop.run_until_complete(uv_server.serve(sockets=[sock]))
