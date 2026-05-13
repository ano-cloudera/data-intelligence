from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.session import SessionMemoryState
from app.services import sql_guardrails
from app.services.llm_router import LLMRouter
from app.services.memory_store import SessionMemoryStore
from app.services.prompt_builder import build_text_to_sql_messages


class SQLGeneratorService:
    def __init__(
        self,
        llm_router: LLMRouter | None = None,
        memory_store: SessionMemoryStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm_router = llm_router or LLMRouter(self.settings)
        self.memory_store = memory_store

    def generate_sql(
        self,
        question: str,
        session_id: str | None = None,
        memory: SessionMemoryState | None = None,
    ) -> dict[str, Any]:
        cleaned_question = question.strip()
        if not cleaned_question:
            raise ValueError("Question must not be empty.")

        active_memory = memory
        if active_memory is None and session_id and self.memory_store is not None:
            active_memory = self.memory_store.get_or_create_session(session_id)

        messages = build_text_to_sql_messages(
            cleaned_question,
            memory=active_memory,
            settings=self.settings,
        )
        raw_generated_sql = self.llm_router.get_client(active_memory).chat(
            messages=messages,
            temperature=0.0,
        )
        cleaned_generated_sql = sql_guardrails.normalize_sql(raw_generated_sql)
        descriptor = self.llm_router.get_descriptor(active_memory)

        if session_id and self.memory_store is not None:
            self.memory_store.append_user_message(session_id, cleaned_question)
            self.memory_store.append_assistant_message(session_id, cleaned_generated_sql)
            self.memory_store.set_last_generated_sql(session_id, cleaned_generated_sql)
            self.memory_store.set_last_intent(session_id, "text-to-sql")

        return {
            "session_id": session_id,
            "original_question": cleaned_question,
            "raw_generated_sql": raw_generated_sql,
            "cleaned_generated_sql": cleaned_generated_sql,
            "model": descriptor.model,
            "deployment": descriptor.deployment,
            "provider": descriptor.provider,
        }
