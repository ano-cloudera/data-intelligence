from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.requests import Request

from app.schemas import (
    RekeningRequest,
    SaldoAnalysisRequest,
    SqlQueryRequest,
    StatusRekeningRequest,
    ToolResponse,
)
import asyncio

from app.impala_client import execute_query_async
from app.tools.cabang_performance import run_cabang_performance
from app.tools.quick_stats import run_quick_stats
from app.tools.rekening_summary import run_rekening_summary
from app.tools.saldo_analysis import run_saldo_analysis
from app.tools.schema import run_get_schema
from app.tools.sql_query import run_sql_query
from app.tools.status_rekening import run_status_rekening_distribution
from app.tools.transaksi_trend import run_transaksi_trend

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = Server("bjt-customer-aggregation")

MCP_TOOLS = [
    Tool(
        name="quick_stats",
        description=(
            "GUNAKAN INI PERTAMA untuk semua pertanyaan overview, ringkasan, atau statistik umum. "
            "Return 4 ringkasan sekaligus: "
            "(1) jumlah & avg saldo per status rekening (Aktif/Dormant/Tutup), "
            "(2) distribusi cluster segmen nasabah (Silent Mature/Young Syariah Digital/Konvensional Produktif), "
            "(3) distribusi RFM segment (Champions/Loyal/Potential/At Risk/Lost) + avg saldo, "
            "(4) top 3 cabang avg saldo tertinggi. "
            "Gunakan untuk: 'overview', 'ringkasan', 'statistik rekening', 'segmen nasabah', "
            "'berapa rekening dormant', 'rfm segment', 'cluster nasabah'. Tidak perlu parameter."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_schema",
        description=(
            "Dapatkan nama tabel, daftar kolom, tipe data, dan aturan query. "
            "Panggil HANYA sebelum sql_query jika belum tahu nama kolom. "
            "Jangan panggil tool ini untuk pertanyaan analitik — gunakan tool lain."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="cabang_performance",
        description=(
            "Performa semua cabang: total rekening, jumlah aktif/dormant/tutup, persentase dormant, "
            "rata-rata saldo, rata-rata transaksi, rata-rata hari sejak transaksi, rekening tidak aktif >180 hari. "
            "Gunakan untuk: 'performa cabang', 'cabang mana paling banyak dormant', "
            "'top cabang tidak aktif', 'persentase tidak aktif per cabang', 'ranking cabang'. "
            "Tidak perlu parameter — return semua cabang, sort/filter di sisi agent."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="transaksi_trend",
        description=(
            "Tren aktivitas transaksi per jenis rekening: "
            "jumlah aktif <=30 hari, kurang aktif 31-180 hari, tidak aktif >180 hari, "
            "rata-rata hari sejak transaksi, persentase tidak aktif. "
            "Gunakan untuk: 'tren aktivitas per jenis rekening', 'rekening tidak aktif per produk', "
            "'aktivitas Tabungan vs Giro', 'berapa persen tidak aktif per jenis rekening'. "
            "Kosongkan jenis_rekening untuk semua jenis sekaligus."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "jenis_rekening": {
                    "type": "string",
                    "description": "Filter by jenis rekening. Kosongkan untuk semua.",
                }
            },
        },
    ),
    Tool(
        name="status_rekening_distribution",
        description=(
            "Distribusi jumlah rekening per status (Aktif/Dormant/Tutup), per jenis rekening dan cabang. "
            "Return: avg saldo dan avg hari sejak transaksi per grup. "
            "Gunakan untuk: 'distribusi status rekening', 'berapa rekening aktif/dormant per cabang', "
            "'breakdown status per jenis rekening'. "
            "Parameter opsional: jenis_rekening, cabang (kode cabang)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "jenis_rekening": {"type": "string", "description": "Filter jenis rekening"},
                "cabang": {"type": "string", "description": "Kode cabang, contoh: 611"},
            },
        },
    ),
    Tool(
        name="saldo_analysis",
        description=(
            "Analisis saldo dan aktivitas per jenis dan/atau status rekening. "
            "Return: jumlah rekening, avg/min/max saldo, avg transaksi, avg hari sejak transaksi, "
            "avg rasio kredit, rekening aktif vs tidak aktif >180 hari. "
            "Gunakan untuk: 'rata-rata saldo Tabungan aktif', 'jumlah rekening Deposito dormant', "
            "'perbandingan saldo aktif vs dormant vs tutup', 'avg saldo per status rekening'. "
            "Parameter opsional: jenis_rekening, status_rekening (0=Aktif, 1=Dormant, 2=Tutup)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "jenis_rekening": {"type": "string", "description": "Filter jenis rekening"},
                "status_rekening": {
                    "type": "integer",
                    "description": "0=Aktif, 1=Dormant, 2=Tutup",
                },
            },
        },
    ),
    Tool(
        name="rekening_summary",
        description=(
            "Ringkasan rekening dikelompokkan per cabang, jenis rekening, cluster, RFM segment, "
            "saldo segment, activity level, age group, dan gender. "
            "Return: total rekening, total saldo, avg saldo, avg transaksi, avg hari sejak transaksi, avg RFM score. "
            "Gunakan untuk: 'top rekening per cluster', 'rekening Champions per cabang', "
            "'rekening Tabungan aktif', 'distribusi rekening per segmen', 'rekening dengan saldo tertinggi'. "
            "Parameter opsional: cif, jenis_rekening, status_rekening (0/1/2), limit (default 20, max 100)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "cif": {"type": "string", "description": "Filter by CIF nasabah"},
                "jenis_rekening": {"type": "string", "description": "Filter jenis rekening"},
                "status_rekening": {"type": "integer", "description": "0=Aktif, 1=Dormant, 2=Tutup"},
                "limit": {"type": "integer", "description": "Max rows (1-100), default 20"},
            },
        },
    ),
    Tool(
        name="sql_query",
        description=(
            "Jalankan SELECT query bebas ke tabel customer_segments_staging. "
            "Gunakan HANYA jika tool lain tidak cukup. "
            "Kolom numerik sudah native type (DOUBLE/BIGINT/INT) — tidak perlu CAST. "
            "Wajib panggil get_schema dulu jika belum tahu nama kolom."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SELECT SQL — gunakan nama tabel: customer_segments_staging",
                }
            },
            "required": ["sql"],
        },
    ),
]


def _format_result(result: dict[str, Any]) -> str:
    """Format tool result as plain text table — readable in Agent Studio monospace output."""
    if "error" in result:
        return f"ERROR: {result['error']}"

    if "schema_info" in result:
        return result["schema_info"]
    if "summary" in result:
        return result["summary"]

    rows = result.get("rows", [])
    row_count = result.get("row_count", len(rows))

    if not rows:
        return "Tidak ada data ditemukan."

    cols = list(rows[0].keys())
    col_widths = {c: max(len(c), max(len(str(row.get(c, ""))) for row in rows)) for c in cols}
    header = "  ".join(c.upper().ljust(col_widths[c]) for c in cols)
    separator = "  ".join("-" * col_widths[c] for c in cols)
    data_lines = [
        "  ".join(str(row.get(c, "")).ljust(col_widths[c]) for c in cols)
        for row in rows
    ]
    lines = [header, separator] + data_lines + [f"\n({row_count} baris)"]
    return "\n".join(lines)


@mcp.list_tools()
async def list_mcp_tools() -> list[Tool]:
    return MCP_TOOLS


@mcp.call_tool()
async def call_mcp_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    # Tool yang tidak hit Impala — langsung return
    if name == "get_schema":
        result = run_get_schema()
        return [TextContent(type="text", text=_format_result(result))]

    # Semua tool yang hit Impala dijalankan async via thread pool
    try:
        if name == "quick_stats":
            result = await asyncio.to_thread(run_quick_stats)
        elif name == "cabang_performance":
            result = await asyncio.to_thread(run_cabang_performance)
        elif name == "transaksi_trend":
            result = await asyncio.to_thread(
                run_transaksi_trend, arguments.get("jenis_rekening")
            )
        elif name == "status_rekening_distribution":
            result = await asyncio.to_thread(
                run_status_rekening_distribution,
                arguments.get("jenis_rekening"),
                arguments.get("cabang"),
            )
        elif name == "saldo_analysis":
            result = await asyncio.to_thread(
                run_saldo_analysis,
                arguments.get("jenis_rekening"),
                arguments.get("status_rekening"),
            )
        elif name == "rekening_summary":
            result = await asyncio.to_thread(
                run_rekening_summary,
                arguments.get("cif"),
                arguments.get("jenis_rekening"),
                arguments.get("limit", 20),
                arguments.get("status_rekening"),
            )
        elif name == "sql_query":
            result = await asyncio.to_thread(run_sql_query, arguments.get("sql", ""))
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as exc:
        result = {"error": str(exc)}

    return [TextContent(type="text", text=_format_result(result))]


# ---------------------------------------------------------------------------
# SSE transport
# ---------------------------------------------------------------------------

sse = SseServerTransport("/messages/")


async def handle_sse(request: Request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp.run(streams[0], streams[1], mcp.create_initialization_options())


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MCP Server — Customer Aggregation",
    description="MCP tools for customer_aggregation table at Bank Jawa Timur",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/messages/", app=sse.handle_post_message)
app.add_route("/sse", handle_sse, methods=["GET"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "3.0.0", "tools": len(MCP_TOOLS)}


@app.get("/tools")
def list_tools() -> dict:
    return {
        "tools": [
            {"name": t.name, "description": t.description}
            for t in MCP_TOOLS
        ]
    }


# REST endpoints for manual testing
@app.get("/tools/get_schema")
def tool_get_schema():
    return run_get_schema()


@app.get("/tools/cabang_performance")
def tool_cabang_performance():
    return ToolResponse(tool="cabang_performance", result=run_cabang_performance())


@app.post("/tools/transaksi_trend")
def tool_transaksi_trend(payload: dict = {}):
    return ToolResponse(
        tool="transaksi_trend",
        result=run_transaksi_trend(jenis_rekening=payload.get("jenis_rekening")),
    )


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
            status_rekening=payload.status_rekening,
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
