from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(
    title="MCP Server — Customer Aggregation",
    description="MCP tools for customer_aggregation table at Bank Jawa Timur",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TOOLS = [
    {
        "name": "sql_query",
        "description": "Run a generic SELECT query against the customer_aggregation table.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SELECT SQL query against customer_aggregation table",
                }
            },
            "required": ["sql"],
        },
    },
    {
        "name": "rekening_summary",
        "description": "Summary rekening per CIF nasabah: total rekening, jenis, saldo, dan status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cif": {"type": "string", "description": "Filter by CIF nasabah"},
                "jenis_rekening": {
                    "type": "string",
                    "description": "Filter by jenis rekening: Tabungan/Giro/Deposito",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max rows returned (1–100)",
                    "default": 20,
                },
            },
        },
    },
    {
        "name": "saldo_analysis",
        "description": "Analisis distribusi saldo dan pola transaksi kredit/debit per jenis dan status rekening.",
        "inputSchema": {
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
    },
    {
        "name": "status_rekening_distribution",
        "description": "Distribusi status rekening (Aktif/Dormant/Tutup) per jenis rekening dan cabang.",
        "inputSchema": {
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
    },
]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tools")
def list_tools() -> dict:
    return {"tools": TOOLS}


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
