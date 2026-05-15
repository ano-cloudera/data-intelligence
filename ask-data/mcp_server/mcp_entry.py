"""
CAI Application entry point for Bank Jatim MCP Server.

This script is the Application script for the MCP Server CAI Application.
It launches a FastAPI server exposing structured analytics tools.

Required env vars (set in CAI Application):
  IMPALA_HOST         Impala coordinator hostname
  IMPALA_PORT         Impala port (default: 443)
  IMPALA_HTTP_PATH    HTTP path (default: cliservice)
  CDP_USER            CDP username
  CDP_PASS            CDP password
  DB_NAME             Impala database (default: cai_sdx_se_indonesia)
  CHROMA_PERSIST_DIR  Path to ChromaDB persistent storage (default: ./chroma_db)
  CHROMA_COLLECTION   ChromaDB collection name (default: bankjatim_docs)
  EMBED_MODEL         Embedding model name (default: nomic-embed-text)
  OLLAMA_BASE_URL     Ollama base URL for embeddings
  CDSW_APP_PORT/PORT  Port assigned by CAI (auto-detected)
"""

import logging
import os
import subprocess
import sys
from pathlib import Path


def resolve_port() -> int:
    raw_port = os.getenv("CDSW_APP_PORT") or os.getenv("PORT") or "8090"
    try:
        return int(raw_port)
    except ValueError:
        return 8090


def resolve_mcp_dir() -> Path:
    cwd = Path.cwd()

    candidates = [
        cwd / "bank-jawa-timur" / "ask-data" / "mcp_server",
        cwd / "ask-data" / "mcp_server",
        cwd / "mcp_server",
    ]

    try:
        for entry in sorted(cwd.iterdir()):
            if entry.is_dir():
                candidates.append(entry / "ask-data" / "mcp_server")
                candidates.append(entry / "mcp_server")
    except Exception:
        pass

    for c in candidates:
        exists = (c / "app" / "main.py").exists()
        logging.info("  %s -> app/main.py exists=%s", c, exists)
        if exists:
            return c

    logging.error("Could not locate mcp_server dir. cwd=%s", cwd)
    return cwd


def ensure_dependencies(mcp_dir: Path, env: dict) -> None:
    req_file = mcp_dir / "requirements.txt"
    if not req_file.exists():
        return
    try:
        import fastapi  # noqa: F401
        import impala  # noqa: F401
        logging.info("Dependencies already installed.")
    except ImportError:
        logging.warning("Dependencies missing, installing from requirements.txt...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            check=True,
            env=env,
        )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    logging.info("Starting Bank Jatim MCP Server")
    logging.info("Working directory: %s", Path.cwd())

    mcp_dir = resolve_mcp_dir()
    port = resolve_port()

    logging.info("Resolved MCP dir: %s", mcp_dir)
    logging.info("Port: %s", port)

    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{mcp_dir}:{pythonpath}" if pythonpath else str(mcp_dir)

    ensure_dependencies(mcp_dir, env)

    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--log-level", "info",
    ]

    logging.info("Launching MCP server: %s", " ".join(cmd))
    process = subprocess.Popen(cmd, cwd=str(mcp_dir), env=env)
    process.wait()

    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
