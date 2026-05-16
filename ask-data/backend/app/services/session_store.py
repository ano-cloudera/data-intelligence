from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Protocol

from app.core.config import Settings, get_settings
from app.schemas.session import SessionMemoryState, SessionSummaryResponse


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionStore(Protocol):
    def create_session_if_not_exists(self, session_id: str) -> SessionMemoryState: ...

    def get_session(self, session_id: str) -> SessionMemoryState | None: ...

    def update_session(self, session: SessionMemoryState) -> SessionMemoryState: ...

    def delete_expired_sessions(self) -> int: ...

    def delete_session(self, session_id: str) -> bool: ...

    def touch_session(self, session_id: str) -> SessionMemoryState | None: ...

    def list_sessions(self, limit: int = 20) -> list[SessionSummaryResponse]: ...


class InMemorySessionStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._sessions: dict[str, SessionMemoryState] = {}
        self._lock = RLock()

    def create_session_if_not_exists(self, session_id: str) -> SessionMemoryState:
        with self._lock:
            self.delete_expired_sessions()
            session = self._sessions.get(session_id)
            if session is None:
                session = SessionMemoryState(session_id=session_id)
                self._sessions[session_id] = session
            else:
                session.updated_at = utc_now()
            return session.model_copy(deep=True)

    def get_session(self, session_id: str) -> SessionMemoryState | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if self.is_expired(session):
                del self._sessions[session_id]
                return None
            session.updated_at = utc_now()
            return session.model_copy(deep=True)

    def update_session(self, session: SessionMemoryState) -> SessionMemoryState:
        with self._lock:
            session.updated_at = utc_now()
            self._sessions[session.session_id] = session.model_copy(deep=True)
            return self._sessions[session.session_id].model_copy(deep=True)

    def delete_expired_sessions(self) -> int:
        with self._lock:
            expired_ids = [
                session_id
                for session_id, session in self._sessions.items()
                if self.is_expired(session)
            ]
            for session_id in expired_ids:
                del self._sessions[session_id]
            return len(expired_ids)

    def is_expired(self, session: SessionMemoryState) -> bool:
        ttl = timedelta(minutes=self.settings.session_ttl_minutes)
        return utc_now() - session.updated_at > ttl

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def touch_session(self, session_id: str) -> SessionMemoryState | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if self.is_expired(session):
                del self._sessions[session_id]
                return None
            session.updated_at = utc_now()
            return session.model_copy(deep=True)

    def list_sessions(self, limit: int = 20) -> list[SessionSummaryResponse]:
        with self._lock:
            self.delete_expired_sessions()
            ordered = sorted(
                self._sessions.values(),
                key=lambda session: session.updated_at,
                reverse=True,
            )
            return [_build_session_summary(session) for session in ordered[:limit]]


class SQLiteSessionStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._lock = RLock()
        self._db_path = Path(self.settings.session_sqlite_path).expanduser()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def create_session_if_not_exists(self, session_id: str) -> SessionMemoryState:
        with self._lock:
            self.delete_expired_sessions()
            session = self._fetch_session(session_id)
            if session is None:
                session = SessionMemoryState(session_id=session_id)
            else:
                session.updated_at = utc_now()
            self._upsert_session(session)
            return session.model_copy(deep=True)

    def get_session(self, session_id: str) -> SessionMemoryState | None:
        with self._lock:
            session = self._fetch_session(session_id)
            if session is None:
                return None
            if self.is_expired(session):
                self._delete_session(session_id)
                return None
            session.updated_at = utc_now()
            self._upsert_session(session)
            return session.model_copy(deep=True)

    def update_session(self, session: SessionMemoryState) -> SessionMemoryState:
        with self._lock:
            session.updated_at = utc_now()
            self._upsert_session(session)
            return session.model_copy(deep=True)

    def delete_expired_sessions(self) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "SELECT session_id, payload_json FROM sessions"
            )
            expired_ids: list[str] = []
            for row in cursor.fetchall():
                session = self._deserialize_session(row["payload_json"])
                if self.is_expired(session):
                    expired_ids.append(row["session_id"])

            if expired_ids:
                connection.executemany(
                    "DELETE FROM sessions WHERE session_id = ?",
                    [(session_id,) for session_id in expired_ids],
                )
                connection.commit()
            return len(expired_ids)

    def touch_session(self, session_id: str) -> SessionMemoryState | None:
        with self._lock:
            session = self._fetch_session(session_id)
            if session is None:
                return None
            if self.is_expired(session):
                self._delete_session(session_id)
                return None
            session.updated_at = utc_now()
            self._upsert_session(session)
            return session.model_copy(deep=True)

    def list_sessions(self, limit: int = 20) -> list[SessionSummaryResponse]:
        with self._lock:
            self.delete_expired_sessions()
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    SELECT payload_json
                    FROM sessions
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
                return [
                    _build_session_summary(self._deserialize_session(row["payload_json"]))
                    for row in cursor.fetchall()
                ]

    def is_expired(self, session: SessionMemoryState) -> bool:
        ttl = timedelta(minutes=self.settings.session_ttl_minutes)
        return utc_now() - session.updated_at > ttl

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
                ON sessions(updated_at DESC)
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _fetch_session(self, session_id: str) -> SessionMemoryState | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            return self._deserialize_session(row["payload_json"])

    def _upsert_session(self, session: SessionMemoryState) -> None:
        payload_json = self._serialize_session(session)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions (session_id, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    session.session_id,
                    payload_json,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                ),
            )
            connection.commit()

    def _delete_session(self, session_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            connection.commit()

    def delete_session(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        if session is None:
            return False
        self._delete_session(session_id)
        return True

    @staticmethod
    def _serialize_session(session: SessionMemoryState) -> str:
        return session.model_dump_json()

    @staticmethod
    def _deserialize_session(payload_json: str) -> SessionMemoryState:
        return SessionMemoryState.model_validate(json.loads(payload_json))


def _build_session_summary(session: SessionMemoryState) -> SessionSummaryResponse:
    user_messages = [message.content for message in session.messages if message.role == "user"]
    assistant_messages = [
        message.content for message in session.messages if message.role == "assistant"
    ]
    title_source = user_messages[0] if user_messages else session.last_answer or "New conversation"
    return SessionSummaryResponse(
        session_id=session.session_id,
        title=_truncate_text(title_source, 48),
        message_count=len(session.messages),
        last_user_message=user_messages[-1] if user_messages else None,
        last_assistant_message=assistant_messages[-1] if assistant_messages else None,
        last_intent=session.last_intent,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _truncate_text(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"
