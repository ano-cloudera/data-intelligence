from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Protocol

from app.core.config import Settings, get_settings
from app.schemas.analytics import (
    AnalyticsEventRecord,
    AnalyticsEventsResponse,
    AnalyticsModeMetric,
    AnalyticsProviderMetric,
    AnalyticsSummaryResponse,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def estimate_text_tokens(*parts: str | None) -> int:
    text = " ".join(part.strip() for part in parts if isinstance(part, str) and part.strip())
    if not text:
        return 0
    return max(1, round(len(text) / 4))


class AnalyticsStore(Protocol):
    def log_event(
        self,
        *,
        event_type: str,
        endpoint: str,
        session_id: str | None = None,
        mode: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
        success: bool = True,
        guardrails_action: str | None = None,
        visualization_type: str | None = None,
        estimated_prompt_tokens: int = 0,
        estimated_completion_tokens: int = 0,
        question_excerpt: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None: ...

    def get_summary(self, window_days: int = 30) -> AnalyticsSummaryResponse: ...

    def list_events(self, limit: int = 20) -> AnalyticsEventsResponse: ...


class InMemoryAnalyticsStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._events: list[AnalyticsEventRecord] = []
        self._next_id = 1
        self._lock = RLock()

    def log_event(
        self,
        *,
        event_type: str,
        endpoint: str,
        session_id: str | None = None,
        mode: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
        success: bool = True,
        guardrails_action: str | None = None,
        visualization_type: str | None = None,
        estimated_prompt_tokens: int = 0,
        estimated_completion_tokens: int = 0,
        question_excerpt: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            record = AnalyticsEventRecord(
                event_id=self._next_id,
                created_at=utc_now(),
                event_type=event_type,
                endpoint=endpoint,
                session_id=session_id,
                mode=mode,
                provider=provider,
                model_name=model_name,
                success=success,
                guardrails_action=guardrails_action,
                visualization_type=visualization_type,
                estimated_prompt_tokens=estimated_prompt_tokens,
                estimated_completion_tokens=estimated_completion_tokens,
                estimated_total_tokens=estimated_prompt_tokens + estimated_completion_tokens,
                question_excerpt=question_excerpt,
                metadata=metadata or {},
            )
            self._events.append(record)
            self._next_id += 1

    def get_summary(self, window_days: int = 30) -> AnalyticsSummaryResponse:
        with self._lock:
            return _build_summary(self._events, window_days=window_days)

    def list_events(self, limit: int = 20) -> AnalyticsEventsResponse:
        with self._lock:
            ordered = sorted(self._events, key=lambda event: event.created_at, reverse=True)
            return AnalyticsEventsResponse(events=ordered[:limit])


class SQLiteAnalyticsStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._lock = RLock()
        self._db_path = Path(self.settings.session_sqlite_path).expanduser()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def log_event(
        self,
        *,
        event_type: str,
        endpoint: str,
        session_id: str | None = None,
        mode: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
        success: bool = True,
        guardrails_action: str | None = None,
        visualization_type: str | None = None,
        estimated_prompt_tokens: int = 0,
        estimated_completion_tokens: int = 0,
        question_excerpt: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO app_events (
                    created_at,
                    event_type,
                    endpoint,
                    session_id,
                    mode,
                    provider,
                    model_name,
                    success,
                    guardrails_action,
                    visualization_type,
                    estimated_prompt_tokens,
                    estimated_completion_tokens,
                    question_excerpt,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    utc_now().isoformat(),
                    event_type,
                    endpoint,
                    session_id,
                    mode,
                    provider,
                    model_name,
                    1 if success else 0,
                    guardrails_action,
                    visualization_type,
                    estimated_prompt_tokens,
                    estimated_completion_tokens,
                    question_excerpt,
                    json.dumps(metadata or {}, ensure_ascii=True),
                ),
            )
            connection.commit()

    def get_summary(self, window_days: int = 30) -> AnalyticsSummaryResponse:
        with self._lock, self._connect() as connection:
            threshold = (utc_now() - timedelta(days=window_days)).isoformat()
            rows = connection.execute(
                """
                SELECT *
                FROM app_events
                WHERE created_at >= ?
                ORDER BY created_at DESC
                """,
                (threshold,),
            ).fetchall()
            events = [_row_to_event(row) for row in rows]
            return _build_summary(events, window_days=window_days)

    def list_events(self, limit: int = 20) -> AnalyticsEventsResponse:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM app_events
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return AnalyticsEventsResponse(events=[_row_to_event(row) for row in rows])

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    session_id TEXT,
                    mode TEXT,
                    provider TEXT,
                    model_name TEXT,
                    success INTEGER NOT NULL,
                    guardrails_action TEXT,
                    visualization_type TEXT,
                    estimated_prompt_tokens INTEGER NOT NULL DEFAULT 0,
                    estimated_completion_tokens INTEGER NOT NULL DEFAULT 0,
                    question_excerpt TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_events_created_at
                ON app_events(created_at DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_app_events_session_id
                ON app_events(session_id)
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection


def _row_to_event(row: sqlite3.Row) -> AnalyticsEventRecord:
    estimated_prompt_tokens = int(row["estimated_prompt_tokens"] or 0)
    estimated_completion_tokens = int(row["estimated_completion_tokens"] or 0)
    metadata_json = row["metadata_json"] or "{}"
    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError:
        metadata = {}

    return AnalyticsEventRecord(
        event_id=int(row["event_id"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        event_type=row["event_type"],
        endpoint=row["endpoint"],
        session_id=row["session_id"],
        mode=row["mode"],
        provider=row["provider"],
        model_name=row["model_name"],
        success=bool(row["success"]),
        guardrails_action=row["guardrails_action"],
        visualization_type=row["visualization_type"],
        estimated_prompt_tokens=estimated_prompt_tokens,
        estimated_completion_tokens=estimated_completion_tokens,
        estimated_total_tokens=estimated_prompt_tokens + estimated_completion_tokens,
        question_excerpt=row["question_excerpt"],
        metadata=metadata if isinstance(metadata, dict) else {},
    )


def _build_summary(events: list[AnalyticsEventRecord], window_days: int) -> AnalyticsSummaryResponse:
    mode_counts = Counter(event.mode for event in events if event.mode)
    provider_counts = Counter(event.provider for event in events if event.provider)
    question_events = [event for event in events if event.event_type in {"chat-query", "chat-answer"}]
    latest_event = events[0].created_at if events else None

    return AnalyticsSummaryResponse(
        window_days=window_days,
        total_events=len(events),
        total_sessions=len({event.session_id for event in events if event.session_id}),
        total_questions=len(question_events),
        sql_requests=mode_counts.get("chat-query", 0),
        rag_requests=mode_counts.get("rag", 0),
        conversation_requests=mode_counts.get("conversation", 0),
        visualization_followups=mode_counts.get("visualization-followup", 0),
        visualization_responses=sum(1 for event in events if event.visualization_type not in {None, "", "table"}),
        guardrails_blocks=sum(
            1
            for event in events
            if event.mode == "guardrails-block" or event.guardrails_action == "block"
        ),
        provider_selections=sum(1 for event in events if event.event_type == "provider-select"),
        estimated_prompt_tokens=sum(event.estimated_prompt_tokens for event in events),
        estimated_completion_tokens=sum(event.estimated_completion_tokens for event in events),
        estimated_total_tokens=sum(event.estimated_total_tokens for event in events),
        mode_breakdown=[
            AnalyticsModeMetric(mode=mode, count=count)
            for mode, count in mode_counts.most_common()
        ],
        provider_breakdown=[
            AnalyticsProviderMetric(provider=provider, count=count)
            for provider, count in provider_counts.most_common()
        ],
        latest_event_at=latest_event,
    )
