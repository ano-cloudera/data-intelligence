from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SqlQueryRequest(BaseModel):
    sql: str


class DormantRiskRequest(BaseModel):
    segment: str | None = None
    branch_city: str | None = None
    risk_level: str | None = None


class DormantReasonRequest(BaseModel):
    segment: str | None = None
    risk_level: str | None = None


class CampaignRecommendationRequest(BaseModel):
    segment: str | None = None
    dormant_reason_code: str | None = None
    risk_level: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    collection_name: str | None = None


class ToolResponse(BaseModel):
    tool: str
    result: dict[str, Any]
