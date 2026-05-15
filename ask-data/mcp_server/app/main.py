from __future__ import annotations

from fastapi import FastAPI

from app.schemas import (
    CampaignRecommendationRequest,
    DormantReasonRequest,
    DormantRiskRequest,
    RagSearchRequest,
    SqlQueryRequest,
    ToolResponse,
)
from app.tools.campaign import get_campaign_recommendation, get_campaign_summary_by_reason
from app.tools.dormant_risk import get_dormant_reason_breakdown, get_dormant_risk_summary
from app.tools.rag_search import search_policy_documents
from app.tools.sql_query import run_sql_query

app = FastAPI(
    title="Bank Jatim MCP Server",
    description="Model Context Protocol server — structured tools for customer dormant analytics",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "mcp-server"}


@app.get("/tools")
def list_tools():
    """List all available MCP tools with description and input schema."""
    return {
        "tools": [
            {
                "name": "sql_query",
                "description": "Execute a raw SELECT SQL query against customer_dormant_segment table.",
                "endpoint": "POST /tools/sql_query",
                "input": {"sql": "string — SELECT statement"},
            },
            {
                "name": "dormant_risk_summary",
                "description": "Get dormant risk level distribution, optionally filtered by segment, city, or risk level.",
                "endpoint": "POST /tools/dormant_risk_summary",
                "input": {"segment": "string?", "city": "string?", "risk_level": "HIGH|MEDIUM|LOW|NONE?"},
            },
            {
                "name": "dormant_reason_breakdown",
                "description": "Get count breakdown of dormant reason codes, optionally filtered by segment or risk level.",
                "endpoint": "POST /tools/dormant_reason_breakdown",
                "input": {"segment": "string?", "risk_level": "string?"},
            },
            {
                "name": "campaign_recommendation",
                "description": "Get top dormant customers with recommended campaign action and channel.",
                "endpoint": "POST /tools/campaign_recommendation",
                "input": {"segment": "string?", "dormant_reason_code": "string?", "risk_level": "string?", "limit": "int (default 20)"},
            },
            {
                "name": "campaign_summary_by_reason",
                "description": "Aggregate campaign priority and recommended action per dormant reason code.",
                "endpoint": "GET /tools/campaign_summary_by_reason",
                "input": {},
            },
            {
                "name": "rag_search",
                "description": "Semantic search across Bank Jatim policy documents in ChromaDB.",
                "endpoint": "POST /tools/rag_search",
                "input": {"query": "string", "top_k": "int (default 5)", "collection_name": "string?"},
            },
        ]
    }


# --- Tool endpoints ---

@app.post("/tools/sql_query", response_model=ToolResponse)
def tool_sql_query(req: SqlQueryRequest):
    return ToolResponse(tool="sql_query", result=run_sql_query(req.sql))


@app.post("/tools/dormant_risk_summary", response_model=ToolResponse)
def tool_dormant_risk_summary(req: DormantRiskRequest):
    return ToolResponse(
        tool="dormant_risk_summary",
        result=get_dormant_risk_summary(
            segment=req.segment,
            city=req.city,
            risk_level=req.risk_level,
        ),
    )


@app.post("/tools/dormant_reason_breakdown", response_model=ToolResponse)
def tool_dormant_reason_breakdown(req: DormantReasonRequest):
    return ToolResponse(
        tool="dormant_reason_breakdown",
        result=get_dormant_reason_breakdown(
            segment=req.segment,
            risk_level=req.risk_level,
        ),
    )


@app.post("/tools/campaign_recommendation", response_model=ToolResponse)
def tool_campaign_recommendation(req: CampaignRecommendationRequest):
    return ToolResponse(
        tool="campaign_recommendation",
        result=get_campaign_recommendation(
            segment=req.segment,
            dormant_reason_code=req.dormant_reason_code,
            risk_level=req.risk_level,
            limit=req.limit,
        ),
    )


@app.get("/tools/campaign_summary_by_reason", response_model=ToolResponse)
def tool_campaign_summary_by_reason():
    return ToolResponse(
        tool="campaign_summary_by_reason",
        result=get_campaign_summary_by_reason(),
    )


@app.post("/tools/rag_search", response_model=ToolResponse)
def tool_rag_search(req: RagSearchRequest):
    return ToolResponse(
        tool="rag_search",
        result=search_policy_documents(
            query=req.query,
            top_k=req.top_k,
            collection_name=req.collection_name,
        ),
    )
