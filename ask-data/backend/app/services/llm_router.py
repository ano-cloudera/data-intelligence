from __future__ import annotations

import os

from app.core.config import Settings, get_settings
from app.schemas.session import SessionMemoryState
from app.services.llm_client import AzureOpenAIClient, BedrockClient, ChatLLMClient, LLMDescriptor
from app.services.llm_provider_service import LLMProviderService

_LLM_PROVIDER_ENV = "LLM_PROVIDER"


class LLMRouter:
    def __init__(
        self,
        settings: Settings | None = None,
        provider_service: LLMProviderService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.provider_service = provider_service or LLMProviderService(self.settings)

    def _env_provider(self) -> str:
        return os.getenv(_LLM_PROVIDER_ENV, "").strip().lower()

    def get_client(self, session_memory: SessionMemoryState | None = None) -> ChatLLMClient:
        if self._env_provider() == "local_qwen":
            from llm.qwen_client import QwenClient  # noqa: PLC0415
            return QwenClient()

        selection = self.provider_service.resolve_selection(session_memory)
        if selection.provider == "bedrock":
            return BedrockClient(settings=self.settings, model_id=selection.model_id)
        return AzureOpenAIClient(settings=self.settings)

    def get_descriptor(self, session_memory: SessionMemoryState | None = None) -> LLMDescriptor:
        if self._env_provider() == "local_qwen":
            return LLMDescriptor(
                provider="local_qwen",
                model=os.getenv("QWEN_MODEL", "Qwen/Qwen3-8B-AWQ"),
                deployment=os.getenv("QWEN_BASE_URL", "http://localhost:8000/v1"),
            )

        selection = self.provider_service.resolve_selection(session_memory)
        if selection.provider == "bedrock":
            return LLMDescriptor(
                provider="bedrock",
                model=selection.model_name or self.settings.bedrock_model_name,
                deployment=selection.model_id or self.settings.bedrock_model_id,
            )
        return LLMDescriptor(
            provider="azure",
            model=self.settings.azure_openai_model,
            deployment=self.settings.azure_openai_deployment,
        )
