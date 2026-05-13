from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SQLGenerateRequest(BaseModel):
    question: str
    session_id: str | None = None


class SQLExecuteRequest(BaseModel):
    sql: str
    session_id: str | None = None


class ChatQueryRequest(BaseModel):
    question: str
    session_id: str | None = None


class AnswerSource(BaseModel):
    title: str
    document_id: str | None = None
    node_id: str | None = None
    score: float | None = None
    preview_url: str | None = None
    download_url: str | None = None


class VisualizationSpec(BaseModel):
    type: str | None = None
    title: str | None = None
    x_key: str | None = None
    y_key: str | None = None
    series: list[dict[str, Any]] = Field(default_factory=list)
    table_columns: list[str] = Field(default_factory=list)
    table_rows: list[dict[str, Any]] = Field(default_factory=list)
    insight: str | None = None


class ChatAnswerResponse(BaseModel):
    session_id: str | None = None
    original_question: str
    answer: str
    mode: str | None = None
    sources: list[AnswerSource] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    visualization: VisualizationSpec | None = None


class SQLExecutionResponse(BaseModel):
    executed_sql: str
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    limit_applied: bool = False


class SQLGenerationResponse(BaseModel):
    session_id: str | None = None
    original_question: str
    raw_generated_sql: str
    cleaned_generated_sql: str
    provider: str | None = None
    model: str
    deployment: str


class ChatQueryResponse(BaseModel):
    session_id: str | None = None
    original_question: str
    answer: str
    generated_sql: str
    executed_sql: str
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    limit_applied: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    visualization: VisualizationSpec | None = None
