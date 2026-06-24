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
from app.tools.cabang_map import run_cabang_map
from app.tools.cabang_performance import run_cabang_performance
from app.tools.campaign import get_campaign_recommendation, get_campaign_summary_by_reason
from app.tools.cluster_summary import run_cluster_summary
from app.tools.demografis_summary import run_demografis_summary
from app.tools.dormant_risk import get_dormant_reason_breakdown, get_dormant_risk_summary
from app.tools.quick_stats import run_quick_stats
from app.tools.rag_search import search_policy_documents
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
            "Performa cabang: total rekening, jumlah aktif/dormant/tutup, persentase dormant, "
            "rata-rata saldo, rata-rata transaksi, rata-rata hari sejak transaksi, rekening tidak aktif >180 hari. "
            "Gunakan untuk: 'performa cabang', 'top cabang saldo tertinggi', 'distribusi saldo per cabang', "
            "'cabang paling banyak dormant', 'ranking cabang', 'cabang terbaik', 'top N cabang'. "
            "Parameter order_by: 'avg_saldo' (default top saldo), 'dormant' (paling banyak dormant), "
            "'total_rekening', 'tidak_aktif', 'pct_dormant'. "
            "Parameter limit: jumlah cabang yang dikembalikan (default 10, max 50). "
            "Contoh top 3 saldo: order_by='avg_saldo', limit=3."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "order_by": {
                    "type": "string",
                    "description": "Urutan hasil: 'avg_saldo', 'dormant', 'total_rekening', 'tidak_aktif', 'pct_dormant'",
                },
                "limit": {
                    "type": "integer",
                    "description": "Jumlah cabang yang dikembalikan (1-50), default 10",
                },
            },
        },
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
                "cluster_label": {"type": "string", "description": "Filter cluster: 'Silent Mature', 'Young Syariah Digital', 'Konvensional Produktif'"},
                "rfm_segment": {"type": "string", "description": "Filter RFM: 'Champions', 'Loyal', 'Potential', 'At Risk', 'Lost'"},
                "limit": {"type": "integer", "description": "Max rows (1-100), default 20"},
            },
        },
    ),
    Tool(
        name="cluster_summary",
        description=(
            "Ringkasan dan karakteristik per cluster segmentasi nasabah: "
            "jumlah rekening, aktif/dormant/tutup, avg/min/max saldo, avg transaksi, "
            "avg hari sejak transaksi, avg RFM score, avg umur, distribusi gender (pria/wanita). "
            "Gunakan untuk: 'karakteristik Young Syariah Digital', 'profil Silent Mature', "
            "'karakteristik Konvensional Produktif', 'jumlah nasabah per cluster', "
            "'perbandingan 3 cluster', 'statistik cluster', 'detail cluster'. "
            "Parameter opsional: cluster_label untuk filter satu cluster spesifik. "
            "Nilai cluster_label: 'Young Syariah Digital', 'Silent Mature', 'Konvensional Produktif'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "cluster_label": {
                    "type": "string",
                    "description": "Filter satu cluster: 'Young Syariah Digital', 'Silent Mature', 'Konvensional Produktif'. Kosongkan untuk semua cluster.",
                }
            },
        },
    ),
    Tool(
        name="demografis_summary",
        description=(
            "Distribusi demografis nasabah: gender (pria/wanita), kelompok usia (age group), "
            "activity level, avg saldo, avg transaksi per kombinasi demografis. "
            "Gunakan untuk: 'distribusi gender', 'kelompok usia nasabah', 'activity level pria vs wanita', "
            "'perbandingan demografis', 'nasabah berdasarkan usia', 'distribusi age group'. "
            "Tidak perlu parameter."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="cabang_map",
        description=(
            "Return data geospatial per cabang untuk visualisasi PETA Jawa Timur. "
            "Setiap cabang dilengkapi: nama cabang, kota, koordinat lat/lng, total rekening, "
            "jumlah aktif/dormant, persentase dormant, rata-rata saldo. "
            "Gunakan untuk: 'peta cabang', 'sebaran cabang di Jawa Timur', "
            "'cabang mana yang paling banyak dormant di peta', 'visualisasi geografis rekening', "
            "'distribusi cluster per wilayah', 'map cabang', 'tampilkan di peta'. "
            "Parameter metric: 'total' (default), 'dormant', 'avg_saldo', 'pct_dormant'. "
            "Parameter limit: jumlah cabang (default 50, max 200)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Metrik untuk warna marker: 'total', 'dormant', 'avg_saldo', 'pct_dormant'",
                },
                "limit": {
                    "type": "integer",
                    "description": "Jumlah cabang yang dikembalikan (1-200), default 50",
                },
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
    Tool(
        name="dormant_risk_summary",
        description=(
            "Distribusi tingkat risiko dormant nasabah (HIGH/MEDIUM/LOW/NONE). "
            "Return: jumlah nasabah dan persentase per risk level. "
            "Gunakan untuk: 'berapa nasabah HIGH risk', 'distribusi dormant risk', "
            "'nasabah berisiko tinggi', 'risk level breakdown'. "
            "Parameter opsional: segment, city, risk_level."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "segment": {"type": "string", "description": "Filter segment nasabah"},
                "city": {"type": "string", "description": "Filter kota"},
                "risk_level": {"type": "string", "description": "HIGH / MEDIUM / LOW / NONE"},
            },
        },
    ),
    Tool(
        name="dormant_reason_breakdown",
        description=(
            "Breakdown penyebab dormant per reason code. "
            "Return: jumlah nasabah per dormant reason code. "
            "Gunakan untuk: 'kenapa nasabah dormant', 'penyebab dormant terbanyak', "
            "'breakdown reason code dormant'. "
            "Parameter opsional: segment, risk_level."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "segment": {"type": "string", "description": "Filter segment nasabah"},
                "risk_level": {"type": "string", "description": "Filter risk level"},
            },
        },
    ),
    Tool(
        name="campaign_recommendation",
        description=(
            "Rekomendasi campaign untuk nasabah dormant HIGH/MEDIUM risk. "
            "Return: daftar nasabah dengan aksi campaign, channel, dan prioritas yang direkomendasikan. "
            "Gunakan untuk: 'siapa yang harus di-campaign', 'rekomendasi aksi dormant', "
            "'nasabah prioritas campaign', 'next best action'. "
            "Parameter opsional: segment, dormant_reason_code, risk_level, limit (default 20)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "segment": {"type": "string", "description": "Filter segment nasabah"},
                "dormant_reason_code": {"type": "string", "description": "Filter reason code"},
                "risk_level": {"type": "string", "description": "Filter risk level"},
                "limit": {"type": "integer", "description": "Jumlah nasabah (default 20)"},
            },
        },
    ),
    Tool(
        name="campaign_summary_by_reason",
        description=(
            "Ringkasan campaign per dormant reason code: jumlah nasabah, avg saldo, "
            "aksi yang direkomendasikan, dan channel. "
            "Gunakan untuk: 'ringkasan campaign per reason', 'prioritas campaign per penyebab dormant'."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="rag_search",
        description=(
            "Semantic search di dokumen kebijakan Bank Jatim (PDF yang sudah di-upload). "
            "Gunakan untuk: pertanyaan kebijakan bank, regulasi, SOP, peraturan nasabah kredit, "
            "'apa kebijakan...', 'bagaimana prosedur...', 'syarat...', 'ketentuan...'. "
            "Parameter: query (wajib), top_k (default 5), collection_name (opsional)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Pertanyaan atau kata kunci pencarian"},
                "top_k": {"type": "integer", "description": "Jumlah hasil (default 5)"},
                "collection_name": {"type": "string", "description": "Nama collection ChromaDB"},
            },
            "required": ["query"],
        },
    ),
]


_STOP_SIGNAL = (
    "\n\n[TOOL_STATUS: complete | done: true | next_action: FINAL_ANSWER]\n"
    "[INSTRUCTION: Data sudah cukup. Jangan panggil tool lagi. Tulis Final Answer sekarang.]"
)


def _format_result(result: dict[str, Any]) -> str:
    """Format tool result as plain text table — readable in Agent Studio monospace output."""
    import json

    if "error" in result:
        return f"ERROR: {result['error']}" + _STOP_SIGNAL

    if "schema_info" in result:
        return result["schema_info"] + _STOP_SIGNAL
    if "summary" in result:
        return result["summary"] + _STOP_SIGNAL

    # Map visualization — return as JSON so frontend can render
    if result.get("visualization") == "map":
        return json.dumps(result, ensure_ascii=False) + _STOP_SIGNAL

    rows = result.get("rows", [])
    row_count = result.get("row_count", len(rows))

    if not rows:
        return "Tidak ada data ditemukan." + _STOP_SIGNAL

    cols = list(rows[0].keys())
    col_widths = {c: max(len(c), max(len(str(row.get(c, ""))) for row in rows)) for c in cols}
    header = "  ".join(c.upper().ljust(col_widths[c]) for c in cols)
    separator = "  ".join("-" * col_widths[c] for c in cols)
    data_lines = [
        "  ".join(str(row.get(c, "")).ljust(col_widths[c]) for c in cols)
        for row in rows
    ]
    lines = [header, separator] + data_lines + [f"\n({row_count} baris)"]
    return "\n".join(lines) + _STOP_SIGNAL


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
            result = await asyncio.to_thread(
                run_cabang_performance,
                arguments.get("order_by", "dormant"),
                arguments.get("limit", 10),
            )
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
                arguments.get("cluster_label"),
                arguments.get("rfm_segment"),
            )
        elif name == "cluster_summary":
            result = await asyncio.to_thread(
                run_cluster_summary, arguments.get("cluster_label")
            )
        elif name == "demografis_summary":
            result = await asyncio.to_thread(run_demografis_summary)
        elif name == "cabang_map":
            result = await asyncio.to_thread(
                run_cabang_map,
                arguments.get("metric", "total"),
                arguments.get("limit", 50),
            )
        elif name == "sql_query":
            result = await asyncio.to_thread(run_sql_query, arguments.get("sql", ""))
        elif name == "dormant_risk_summary":
            result = await asyncio.to_thread(
                get_dormant_risk_summary,
                arguments.get("segment"),
                arguments.get("city"),
                arguments.get("risk_level"),
            )
        elif name == "dormant_reason_breakdown":
            result = await asyncio.to_thread(
                get_dormant_reason_breakdown,
                arguments.get("segment"),
                arguments.get("risk_level"),
            )
        elif name == "campaign_recommendation":
            result = await asyncio.to_thread(
                get_campaign_recommendation,
                arguments.get("segment"),
                arguments.get("dormant_reason_code"),
                arguments.get("risk_level"),
                arguments.get("limit", 20),
            )
        elif name == "campaign_summary_by_reason":
            result = await asyncio.to_thread(get_campaign_summary_by_reason)
        elif name == "rag_search":
            result = await asyncio.to_thread(
                search_policy_documents,
                arguments.get("query", ""),
                arguments.get("top_k", 5),
                arguments.get("collection_name"),
            )
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
    title="MCP Server — Bank Jawa Timur",
    description="Unified MCP tools: customer aggregation, dormant risk, campaign, RAG search",
    version="4.0.0",
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
    return {"status": "ok", "version": "4.0.0", "tools": len(MCP_TOOLS)}


@app.get("/tools")
def list_tools() -> dict:
    return {
        "tools": [
            {"name": t.name, "description": t.description}
            for t in MCP_TOOLS
        ]
    }


# REST endpoints for manual testing
@app.get("/tools/quick_stats")
def tool_quick_stats():
    return ToolResponse(tool="quick_stats", result=run_quick_stats())


@app.get("/tools/get_schema")
def tool_get_schema():
    return run_get_schema()


@app.get("/tools/cabang_performance")
def tool_cabang_performance(order_by: str = "dormant", limit: int = 10):
    return ToolResponse(tool="cabang_performance", result=run_cabang_performance(order_by, limit))


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


@app.get("/tools/cluster_summary")
def tool_cluster_summary(cluster_label: str | None = None):
    return ToolResponse(tool="cluster_summary", result=run_cluster_summary(cluster_label))


@app.get("/tools/demografis_summary")
def tool_demografis_summary():
    return ToolResponse(tool="demografis_summary", result=run_demografis_summary())


@app.get("/tools/cabang_map")
def tool_cabang_map(metric: str = "total", limit: int = 50):
    return run_cabang_map(metric, limit)


@app.post("/tools/status_rekening_distribution", response_model=ToolResponse)
def tool_status_rekening(payload: StatusRekeningRequest) -> ToolResponse:
    return ToolResponse(
        tool="status_rekening_distribution",
        result=run_status_rekening_distribution(
            jenis_rekening=payload.jenis_rekening,
            cabang=payload.cabang,
        ),
    )


# --- Dormant & Campaign tools ---

class DormantRiskRequest(BaseModel):
    segment: str | None = None
    city: str | None = None
    risk_level: str | None = None

class DormantReasonRequest(BaseModel):
    segment: str | None = None
    risk_level: str | None = None

class CampaignRequest(BaseModel):
    segment: str | None = None
    dormant_reason_code: str | None = None
    risk_level: str | None = None
    limit: int = 20

class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    collection_name: str | None = None

from pydantic import BaseModel

@app.post("/tools/dormant_risk_summary", response_model=ToolResponse)
def tool_dormant_risk_summary(payload: DormantRiskRequest) -> ToolResponse:
    return ToolResponse(
        tool="dormant_risk_summary",
        result=get_dormant_risk_summary(payload.segment, payload.city, payload.risk_level),
    )

@app.post("/tools/dormant_reason_breakdown", response_model=ToolResponse)
def tool_dormant_reason_breakdown(payload: DormantReasonRequest) -> ToolResponse:
    return ToolResponse(
        tool="dormant_reason_breakdown",
        result=get_dormant_reason_breakdown(payload.segment, payload.risk_level),
    )

@app.post("/tools/campaign_recommendation", response_model=ToolResponse)
def tool_campaign_recommendation(payload: CampaignRequest) -> ToolResponse:
    return ToolResponse(
        tool="campaign_recommendation",
        result=get_campaign_recommendation(
            payload.segment, payload.dormant_reason_code, payload.risk_level, payload.limit
        ),
    )

@app.get("/tools/campaign_summary_by_reason", response_model=ToolResponse)
def tool_campaign_summary_by_reason() -> ToolResponse:
    return ToolResponse(tool="campaign_summary_by_reason", result=get_campaign_summary_by_reason())

@app.post("/tools/rag_search", response_model=ToolResponse)
def tool_rag_search(payload: RagSearchRequest) -> ToolResponse:
    return ToolResponse(
        tool="rag_search",
        result=search_policy_documents(payload.query, payload.top_k, payload.collection_name),
    )
