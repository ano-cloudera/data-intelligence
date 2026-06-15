"""
CAI Application entry point for ChromaDB HTTP Server.
chromadb 1.5.x — uses make_system_client + chromadb.server.fastapi app directly.

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
        subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + pkgs_needed, check=True)
    else:
        logging.info("All dependencies already installed.")


ensure_deps()

import asyncio
import chromadb
import nest_asyncio
import uvicorn
from chromadb.config import Settings as ChromaSettings

nest_asyncio.apply()

port = resolve_port()
data_path = resolve_data_path()

logging.info("chromadb version : %s", chromadb.__version__)
logging.info("ChromaDB HTTP Server starting on port %s", port)
logging.info("Data path : %s", data_path)

# Set env vars so chromadb server reads them — do NOT instantiate ChromaFastAPI
# directly as it auto-binds in chromadb 1.5.x
os.environ["IS_PERSISTENT"] = "TRUE"
os.environ["PERSIST_DIRECTORY"] = data_path
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["ALLOW_RESET"] = "FALSE"
os.environ["CHROMA_SERVER_AUTHN_CREDENTIALS_FILE"] = ""
os.environ["CHROMA_SERVER_AUTHN_PROVIDER"] = ""

# Build the ASGI app without starting a server
settings = ChromaSettings(
    is_persistent=True,
    persist_directory=data_path,
    allow_reset=False,
    anonymized_telemetry=False,
)

# chromadb 1.5.x exposes the ASGI app via chromadb.server.fastapi.FastAPI.app()
# but instantiating it may auto-bind. Use the lower-level approach:
# create the FastAPI app object directly from chromadb internals.
try:
    from chromadb.server.fastapi import FastAPI as ChromaServer
    # Patch: override the port ChromaDB uses internally so it doesn't bind CDSW_APP_PORT
    # ChromaFastAPI binds via uvicorn internally only if .run() is called — safe to instantiate
    chroma_server = ChromaServer(settings)
    asgi_app = chroma_server.app()
    logging.info("Using chromadb FastAPI ASGI app")
except Exception as e:
    logging.error("Failed to build chromadb ASGI app: %s", e)
    raise

config = uvicorn.Config(
    app=asgi_app,
    host="0.0.0.0",
    port=port,
    log_level="info",
)
uv_server = uvicorn.Server(config)

logging.info("Starting uvicorn on 0.0.0.0:%s", port)
loop = asyncio.get_event_loop()
loop.run_until_complete(uv_server.serve())
