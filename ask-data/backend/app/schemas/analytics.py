from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsEventRecord(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    event_id: int
    created_at: datetime
    event_type: str
    endpoint: str
    session_id: str | None = None
    mode: str | None = None
    provider: str | None = None
    model_name: str | None = None
    success: bool = True
    guardrails_action: str | None = None
    visualization_type: str | None = None
    estimated_prompt_tokens: int = 0
    estimated_completion_tokens: int = 0
    estimated_total_tokens: int = 0
    question_excerpt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyticsModeMetric(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    mode: str
    count: int


class AnalyticsProviderMetric(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str
    count: int


class AnalyticsSummaryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    window_days: int
    total_events: int = 0
    total_sessions: int = 0
    total_questions: int = 0
    sql_requests: int = 0
    rag_requests: int = 0
    conversation_requests: int = 0
    visualization_followups: int = 0
    visualization_responses: int = 0
    guardrails_blocks: int = 0
    provider_selections: int = 0
    estimated_prompt_tokens: int = 0
    estimated_completion_tokens: int = 0
    estimated_total_tokens: int = 0
    mode_breakdown: list[AnalyticsModeMetric] = Field(default_factory=list)
    provider_breakdown: list[AnalyticsProviderMetric] = Field(default_factory=list)
    latest_event_at: datetime | None = None


class AnalyticsEventsResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    events: list[AnalyticsEventRecord] = Field(default_factory=list)
