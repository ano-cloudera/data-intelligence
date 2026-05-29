from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

try:
    from fastmcp import FastMCP
except ImportError:
    print("fastmcp not installed. Run: pip install fastmcp")
    sys.exit(1)

try:
    from lightmem.memory.lightmem import LightMemory
except ImportError:
    print("lightmem not installed. Run: pip install -e /path/to/LightMem")
    sys.exit(1)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

mcp = FastMCP("BJT LightMem Memory Server")

_lightmem_instance: LightMemory | None = None


def get_lightmem(config_path: str = CONFIG_PATH) -> LightMemory:
    global _lightmem_instance
    if _lightmem_instance is None:
        with open(config_path) as f:
            config = json.load(f)
        _lightmem_instance = LightMemory.from_config(config)
    return _lightmem_instance


@mcp.tool()
def get_timestamp() -> dict:
    """Return current timestamp in ISO format."""
    return {"timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}


@mcp.tool()
def add_memory(
    user_input: str,
    assistant_reply: str,
    timestamp: str | None = None,
    force_segment: bool = True,
    force_extract: bool = True,
) -> dict:
    """
    Simpan pasangan percakapan user-assistant ke LightMem memory.
    Panggil ini setelah setiap interaksi untuk membangun long-term memory.
    """
    try:
        lm = get_lightmem()
        ts = timestamp or datetime.now().strftime("%Y-%m-%d")
        messages = [
            {"role": "user", "content": user_input, "time_stamp": ts},
            {"role": "assistant", "content": assistant_reply, "time_stamp": ts},
        ]
        lm.add_memory(
            messages=messages,
            force_segment=force_segment,
            force_extract=force_extract,
        )
        return {"status": "success", "message": "Memory berhasil disimpan", "timestamp": ts}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def retrieve_memory(query: str, limit: int = 5) -> dict:
    """
    Ambil memory yang relevan berdasarkan query.
    Gunakan untuk recall konteks percakapan sebelumnya.
    """
    try:
        lm = get_lightmem()
        results = lm.retrieve(query, limit=limit)
        return {"status": "success", "memories": results, "count": len(results) if results else 0}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def offline_update(
    top_k: int = 5,
    keep_top_n: int = 3,
    score_threshold: float = 0.8,
) -> dict:
    """
    Jalankan offline update untuk konsolidasi dan deduplikasi memory.
    Jalankan secara berkala (misal setelah 10 sesi).
    """
    try:
        lm = get_lightmem()
        lm.construct_update_queue_all_entries()
        lm.offline_update_all_entries(score_threshold=score_threshold)
        return {"status": "success", "message": "Offline update selesai"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def show_memory_status() -> dict:
    """Tampilkan status dan konfigurasi LightMem instance saat ini."""
    try:
        lm = get_lightmem()
        return {
            "status": "success",
            "instance": str(lm),
            "config_path": CONFIG_PATH,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="BJT LightMem MCP Server")
    parser.add_argument("--config", type=str, default=CONFIG_PATH, help="Path to config.json")
    parser.add_argument("--port", type=int, default=int(os.environ.get("CDSW_APP_PORT", 8095)), help="Port")
    args = parser.parse_args()

    global CONFIG_PATH
    CONFIG_PATH = args.config

    print(f"Starting BJT LightMem MCP Server on port {args.port}")
    print(f"Config: {args.config}")
    mcp.run(transport="http", port=args.port, single_thread=True)


if __name__ == "__main__":
    main()
