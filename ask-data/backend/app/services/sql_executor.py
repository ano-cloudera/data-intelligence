from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.db.connection import ImpalaConnectionError, ImpalaQueryError, run_query_with_metadata
from app.services.sql_guardrails import SQLValidationError, validate_and_prepare_sql


class SQLExecutionError(RuntimeError):
    """Raised when validated SQL execution fails."""


class SQLExecutorService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def execute(self, sql: str) -> dict[str, Any]:
        validated_sql, limit_applied = validate_and_prepare_sql(sql, self.settings)
        try:
            query_result = run_query_with_metadata(validated_sql)
        except (ImpalaConnectionError, ImpalaQueryError) as exc:
            raise SQLExecutionError(str(exc)) from exc

        rows = query_result["rows"]
        preview_rows = rows[: self.settings.sql_max_preview_rows]
        truncated = len(rows) > self.settings.sql_max_preview_rows

        return {
            "executed_sql": validated_sql,
            "columns": query_result["columns"],
            "rows": preview_rows,
            "row_count": len(rows),
            "truncated": truncated,
            "limit_applied": limit_applied,
        }
