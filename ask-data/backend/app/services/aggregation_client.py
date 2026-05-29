from __future__ import annotations

import httpx

from app.core.config import Settings, get_settings

_TIMEOUT = 60.0

TOOL_ENDPOINTS: dict[str, tuple[str, str]] = {
    "quick_stats":                  ("GET",  "/tools/quick_stats"),
    "get_schema":                   ("GET",  "/tools/get_schema"),
    "cluster_summary":              ("GET",  "/tools/cluster_summary"),
    "demografis_summary":           ("GET",  "/tools/demografis_summary"),
    "cabang_performance":           ("GET",  "/tools/cabang_performance"),
    "transaksi_trend":              ("POST", "/tools/transaksi_trend"),
    "status_rekening_distribution": ("POST", "/tools/status_rekening_distribution"),
    "saldo_analysis":               ("POST", "/tools/saldo_analysis"),
    "rekening_summary":             ("POST", "/tools/rekening_summary"),
    "sql_query":                    ("POST", "/tools/sql_query"),
}


def call_aggregation_tool(
    tool_name: str,
    params: dict | None = None,
    settings: Settings | None = None,
) -> dict:
    cfg = settings or get_settings()
    base_url = (cfg.mcp_aggregation_url or "").rstrip("/")
    if not base_url:
        return {"error": "MCP_AGGREGATION_URL tidak dikonfigurasi"}

    if tool_name not in TOOL_ENDPOINTS:
        return {"error": f"Tool tidak dikenal: {tool_name}"}

    method, path = TOOL_ENDPOINTS[tool_name]
    url = base_url + path
    payload = params or {}

    # Filter out None values so optional params don't pollute query string / body
    clean_payload = {k: v for k, v in payload.items() if v is not None}

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            if method == "GET":
                resp = client.get(url, params=clean_payload if clean_payload else None)
            else:
                resp = client.post(url, json=clean_payload)
        resp.raise_for_status()
        return resp.json()
    except httpx.TimeoutException:
        return {"error": f"Timeout memanggil tool {tool_name}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code} dari tool {tool_name}"}
    except Exception as e:
        return {"error": str(e)}


def list_available_tools(settings: Settings | None = None) -> dict:
    cfg = settings or get_settings()
    base_url = (cfg.mcp_aggregation_url or "").rstrip("/")
    if not base_url:
        return {"error": "MCP_AGGREGATION_URL tidak dikonfigurasi"}
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{base_url}/tools")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}
