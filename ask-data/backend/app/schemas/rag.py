from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.session import RagQueryConfiguration


class RagModelOption(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_id: str
    name: str
    available: bool = True
    replica_count: int = 0
    tool_calling_supported: bool = False


class RagKnowledgeBaseOption(BaseModel):
    id: int
    name: str
    description: str | None = None
    document_count: int = 0
    embedding_model: str | None = None
    summarization_model: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagOptionsResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    enabled: bool
    model_source: str | None = None
    chat_models: list[RagModelOption] = Field(default_factory=list)
    rerank_models: list[RagModelOption] = Field(default_factory=list)
    knowledge_bases: list[RagKnowledgeBaseOption] = Field(default_factory=list)


class RagSessionConfigRequest(BaseModel):
    session_id: str
    enabled: bool = False
    session_name: str = "ask-data-rag-session"
    project_id: int | None = None
    knowledge_base_id: int | None = None
    knowledge_base_name: str | None = None
    inference_model_id: str | None = None
    inference_model_name: str | None = None
    rerank_model_id: str | None = None
    rerank_model_name: str | None = None
    response_chunks: int = 10
    query_configuration: RagQueryConfiguration = Field(default_factory=RagQueryConfiguration)


class RagSessionConfigResponse(BaseModel):
    session_id: str
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
