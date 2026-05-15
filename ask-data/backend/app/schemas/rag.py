from __future__ import annotations

from pydantic import BaseModel, Field


class RagCollectionOption(BaseModel):
    name: str
    document_count: int = 0


class RagOptionsResponse(BaseModel):
    enabled: bool
    collections: list[RagCollectionOption] = Field(default_factory=list)


class RagSessionConfigRequest(BaseModel):
    session_id: str
    enabled: bool = False
    collection_name: str | None = None
    top_k: int = 5


class RagSessionConfigResponse(BaseModel):
    session_id: str
    enabled: bool = False
    collection_name: str | None = None
    top_k: int = 5
