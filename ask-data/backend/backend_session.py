from __future__ import annotations

import logging
import os

import uvicorn


def resolve_port() -> int:
    raw_port = os.getenv("APP_PORT") or os.getenv("PORT") or "8000"
    try:
        return int(raw_port)
    except ValueError:
        return 8000


def main() -> None:
    port = resolve_port()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.info("Starting ask-data backend session on 0.0.0.0:%s", port)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
