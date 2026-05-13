from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LLMSelectionState(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    provider: str = "azure"
    model_id: str | None = None
    model_name: str | None = None


class LLMProviderOption(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    provider: str
    label: str
    model_id: str
    model_name: str
    available: bool = True
    description: str | None = None


class LLMProviderOptionsResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    session_id: str | None = None
    active_provider: str
    active_model_id: str | None = None
    active_model_name: str | None = None
    options: list[LLMProviderOption] = Field(default_factory=list)


class LLMProviderSelectionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    session_id: str
    provider: str
    model_id: str | None = None


class LLMProviderSelectionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    session_id: str
    active_provider: str
    active_model_id: str | None = None
    active_model_name: str | None = None
