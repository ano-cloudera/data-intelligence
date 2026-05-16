from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.llm import LLMSelectionState
from app.schemas.rag import RagSessionConfigRequest  # noqa: F401 — used in set_rag_config type hint
from app.schemas.session import (
    ChatMessage,
    RagSessionConfigState,
    ResultPreviewContext,
    SessionMemoryState,
    SessionSummaryResponse,
    TableLockState,
    utc_now,
)
from app.services.session_store import InMemorySessionStore, SessionStore


class SessionMemoryStore:
    def __init__(
        self,
        session_store: SessionStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.session_store = session_store or InMemorySessionStore(self.settings)

    def get_or_create_session(self, session_id: str) -> SessionMemoryState:
        return self.session_store.create_session_if_not_exists(session_id)

    def append_user_message(self, session_id: str, content: str) -> SessionMemoryState:
        return self._append_message(session_id, role="user", content=content)

    def append_assistant_message(self, session_id: str, content: str) -> SessionMemoryState:
        return self._append_message(session_id, role="assistant", content=content)

    def fetch_recent_history(self, session_id: str) -> list[ChatMessage]:
        session = self.session_store.get_session(session_id)
        if session is None:
            return []
        return session.messages[-self.settings.memory_max_history :]

    def set_last_generated_sql(self, session_id: str, sql: str) -> SessionMemoryState:
        session = self.get_or_create_session(session_id)
        session.last_generated_sql = sql
        return self.session_store.update_session(session)

    def get_last_generated_sql(self, session_id: str) -> str | None:
        session = self.session_store.get_session(session_id)
        return None if session is None else session.last_generated_sql

    def set_last_answer(self, session_id: str, answer: str) -> SessionMemoryState:
        session = self.get_or_create_session(session_id)
        session.last_answer = answer
        return self.session_store.update_session(session)

    def get_last_answer(self, session_id: str) -> str | None:
        session = self.session_store.get_session(session_id)
        return None if session is None else session.last_answer

    def set_last_result_preview(
        self,
        session_id: str,
        columns: list[str],
        rows: list[dict[str, Any]],
        row_count: int | None = None,
        truncated: bool = False,
    ) -> SessionMemoryState:
        session = self.get_or_create_session(session_id)
        preview = ResultPreviewContext(
            columns=columns,
            rows=rows,
            row_count=row_count if row_count is not None else len(rows),
            truncated=truncated,
        )
        session.last_result_preview = preview
        return self.session_store.update_session(session)

    def get_last_result_preview(self, session_id: str) -> ResultPreviewContext | None:
        session = self.session_store.get_session(session_id)
        return None if session is None else session.last_result_preview

    def set_last_intent(self, session_id: str, intent: str) -> SessionMemoryState:
        session = self.get_or_create_session(session_id)
        session.last_intent = intent
        return self.session_store.update_session(session)

    def get_last_intent(self, session_id: str) -> str | None:
        session = self.session_store.get_session(session_id)
        return None if session is None else session.last_intent

    def get_session_state(self, session_id: str) -> SessionMemoryState | None:
        return self.session_store.get_session(session_id)

    def list_sessions(self, limit: int = 20) -> list[SessionSummaryResponse]:
        return self.session_store.list_sessions(limit=limit)

    def delete_session(self, session_id: str) -> bool:
        return self.session_store.delete_session(session_id)

    def set_llm_selection(
        self,
        session_id: str,
        selection: LLMSelectionState,
    ) -> SessionMemoryState:
        session = self.get_or_create_session(session_id)
        session.llm_selection = selection
        return self.session_store.update_session(session)

    def get_llm_selection(self, session_id: str) -> LLMSelectionState | None:
        session = self.session_store.get_session(session_id)
        return None if session is None else session.llm_selection

    def set_rag_config(
        self,
        payload: RagSessionConfigRequest,
        rag_session_id: int | None = None,
    ) -> SessionMemoryState:
        session = self.get_or_create_session(payload.session_id)
        session.rag_config = RagSessionConfigState(
            enabled=payload.enabled,
            collection_name=payload.collection_name,
            top_k=payload.top_k,
            updated_at=utc_now(),
        )
        return self.session_store.update_session(session)

    def get_rag_config(self, session_id: str) -> RagSessionConfigState | None:
        session = self.session_store.get_session(session_id)
        return None if session is None else session.rag_config

    def set_table_lock(self, session_id: str, locked_table: str | None) -> SessionMemoryState:
        session = self.get_or_create_session(session_id)
        session.table_lock = TableLockState(locked_table=locked_table, updated_at=utc_now())
        return self.session_store.update_session(session)

    def get_table_lock(self, session_id: str) -> TableLockState | None:
        session = self.session_store.get_session(session_id)
        return None if session is None else session.table_lock

    def _append_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> SessionMemoryState:
        session = self.get_or_create_session(session_id)
        session.messages.append(ChatMessage(role=role, content=content))
        session.messages = session.messages[-self.settings.memory_max_history :]
        return self.session_store.update_session(session)
