from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.requests import Request
from starlette.routing import Mount

from app.schemas import (
    RekeningRequest,
    SaldoAnalysisRequest,
    SqlQueryRequest,
    StatusRekeningRequest,
    ToolResponse,
)
from app.tools.rekening_summary import run_rekening_summary
from app.tools.saldo_analysis import run_saldo_analysis
from app.tools.sql_query import run_sql_query
from app.tools.status_rekening import run_status_rekening_distribution

# ---------------------------------------------------------------------------
# MCP Server (SSE transport — untuk Agent Studio via mcp-proxy)
# ---------------------------------------------------------------------------

mcp = Server("bjt-customer-aggregation")


@mcp.list_tools()
async def list_mcp_tools() -> list[Tool]:
    return [
        Tool(
            name="sql_query",
            description="Run a generic SELECT query against the customer_aggregation table.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SELECT SQL query against customer_aggregation table",
                    }
                },
                "required": ["sql"],
            },
        ),
        Tool(
            name="rekening_summary",
            description="Summary rekening per CIF nasabah: total rekening, jenis, saldo, dan status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cif": {"type": "string", "description": "Filter by CIF nasabah"},
                    "jenis_rekening": {
                        "type": "string",
                        "description": "Filter by jenis rekening: Tabungan/Giro/Deposito",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max rows returned (1-100)",
                        "default": 20,
                    },
                },
            },
        ),
        Tool(
            name="saldo_analysis",
            description="Analisis distribusi saldo dan pola transaksi kredit/debit per jenis dan status rekening.",
            inputSchema={
                "type": "object",
                "properties": {
                    "jenis_rekening": {
                        "type": "string",
                        "description": "Filter by jenis rekening: Tabungan/Giro/Deposito",
                    },
                    "status_rekening": {
                        "type": "integer",
                        "description": "Filter by status: 0=Aktif, 1=Dormant, 2=Tutup",
                    },
                },
            },
        ),
        Tool(
            name="status_rekening_distribution",
            description="Distribusi status rekening (Aktif/Dormant/Tutup) per jenis rekening dan cabang.",
            inputSchema={
                "type": "object",
                "properties": {
                    "jenis_rekening": {
                        "type": "string",
                        "description": "Filter by jenis rekening: Tabungan/Giro/Deposito",
                    },
                    "cabang": {
                        "type": "string",
                        "description": "Filter by kode cabang",
                    },
                },
            },
        ),
    ]


@mcp.call_tool()
async def call_mcp_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "sql_query":
        result = run_sql_query(arguments.get("sql", ""))
    elif name == "rekening_summary":
        result = run_rekening_summary(
            cif=arguments.get("cif"),
            jenis_rekening=arguments.get("jenis_rekening"),
            limit=arguments.get("limit", 20),
        )
    elif name == "saldo_analysis":
        result = run_saldo_analysis(
            jenis_rekening=arguments.get("jenis_rekening"),
            status_rekening=arguments.get("status_rekening"),
        )
    elif name == "status_rekening_distribution":
        result = run_status_rekening_distribution(
            jenis_rekening=arguments.get("jenis_rekening"),
            cabang=arguments.get("cabang"),
        )
    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


# ---------------------------------------------------------------------------
# SSE transport — mount di /sse
# ---------------------------------------------------------------------------

sse = SseServerTransport("/messages/")


async def handle_sse(request: Request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp.run(streams[0], streams[1], mcp.create_initialization_options())


# ---------------------------------------------------------------------------
# FastAPI app (HTTP REST — tetap ada untuk test manual & health check)
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MCP Server — Customer Aggregation",
    description="MCP tools for customer_aggregation table at Bank Jawa Timur",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount SSE message handler
app.mount("/messages/", app=sse.handle_post_message)

# SSE connect endpoint
app.add_route("/sse", handle_sse, methods=["GET"])


# --- REST endpoints (tetap bisa dipakai untuk test manual) ---

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tools")
def list_tools() -> dict:
    return {
        "tools": [
            {"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
            for t in [
                Tool(name="sql_query", description="Run a generic SELECT query against the customer_aggregation table.", inputSchema={}),
                Tool(name="rekening_summary", description="Summary rekening per CIF nasabah.", inputSchema={}),
                Tool(name="saldo_analysis", description="Analisis distribusi saldo dan pola transaksi.", inputSchema={}),
                Tool(name="status_rekening_distribution", description="Distribusi status rekening per jenis dan cabang.", inputSchema={}),
            ]
        ]
    }


@app.post("/tools/sql_query", response_model=ToolResponse)
def tool_sql_query(payload: SqlQueryRequest) -> ToolResponse:
    return ToolResponse(tool="sql_query", result=run_sql_query(payload.sql))


@app.post("/tools/rekening_summary", response_model=ToolResponse)
def tool_rekening_summary(payload: RekeningRequest) -> ToolResponse:
    return ToolResponse(
        tool="rekening_summary",
        result=run_rekening_summary(
            cif=payload.cif,
            jenis_rekening=payload.jenis_rekening,
            limit=payload.limit,
        ),
    )


@app.post("/tools/saldo_analysis", response_model=ToolResponse)
def tool_saldo_analysis(payload: SaldoAnalysisRequest) -> ToolResponse:
    return ToolResponse(
        tool="saldo_analysis",
        result=run_saldo_analysis(
            jenis_rekening=payload.jenis_rekening,
            status_rekening=payload.status_rekening,
        ),
    )


@app.post("/tools/status_rekening_distribution", response_model=ToolResponse)
def tool_status_rekening(payload: StatusRekeningRequest) -> ToolResponse:
    return ToolResponse(
        tool="status_rekening_distribution",
        result=run_status_rekening_distribution(
            jenis_rekening=payload.jenis_rekening,
            cabang=payload.cabang,
        ),
    )
