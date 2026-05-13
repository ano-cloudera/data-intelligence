from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.llm import LLMSelectionState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=utc_now)


class ResultPreviewContext(BaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    captured_at: datetime = Field(default_factory=utc_now)


class RagQueryConfiguration(BaseModel):
    enable_hyde: bool = False
    enable_summary_filter: bool = True
    enable_tool_calling: bool = False
    disable_streaming: bool = False
    selected_tools: list[str] = Field(default_factory=list)


class RagSessionConfigState(BaseModel):
    enabled: bool = False
    session_name: str = "ask-data-rag-session"
    project_id: int | None = None
    knowledge_base_id: int | None = None
    knowledge_base_name: str | None = None
    rag_session_id: int | None = None
    inference_model_id: str | None = None
    inference_model_name: str | None = None
    rerank_model_id: str | None = None
    rerank_model_name: str | None = None
    response_chunks: int = 10
    query_configuration: RagQueryConfiguration = Field(default_factory=RagQueryConfiguration)
    updated_at: datetime = Field(default_factory=utc_now)


class SessionMemoryState(BaseModel):
    session_id: str
    messages: list[ChatMessage] = Field(default_factory=list)
    last_generated_sql: str | None = None
    last_answer: str | None = None
    last_result_preview: ResultPreviewContext | None = None
    last_intent: str | None = None
    llm_selection: LLMSelectionState = Field(default_factory=LLMSelectionState)
    rag_config: RagSessionConfigState | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class SessionSummaryResponse(BaseModel):
    session_id: str
    title: str
    message_count: int = 0
    last_user_message: str | None = None
    last_assistant_message: str | None = None
    last_intent: str | None = None
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionSummaryResponse] = Field(default_factory=list)


class SessionDetailResponse(BaseModel):
    session: SessionMemoryState
