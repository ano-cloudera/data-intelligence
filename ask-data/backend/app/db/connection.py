from __future__ import annotations

from contextlib import closing
from typing import Any

from impala.dbapi import connect

from app.core.config import get_settings


class ImpalaConnectionError(RuntimeError):
    """Raised when the Impala connection cannot be established."""


class ImpalaQueryError(RuntimeError):
    """Raised when an Impala query fails."""


def get_impala_connection():
    settings = get_settings()
    if not settings.is_impala_configured:
        raise ImpalaConnectionError(
            "Impala environment variables are incomplete. "
            "Set IMPALA_HOST, IMPALA_HTTP_PATH, DB_NAME, CDP_USER, and CDP_PASS."
        )

    try:
        return connect(
            host=settings.impala_host,
            port=settings.impala_port,
            database=settings.impala_db,
            user=settings.impala_user,
            password=settings.impala_password,
            use_ssl=True,
            auth_mechanism="PLAIN",
            http_path=settings.impala_http_path,
            use_http_transport=True,
        )
    except Exception as exc:
        raise ImpalaConnectionError(f"Unable to connect to Impala: {exc}") from exc


def run_query(query: str) -> list[dict[str, Any]]:
    result = run_query_with_metadata(query)
    return result["rows"]


def run_query_with_metadata(query: str) -> dict[str, Any]:
    try:
        with closing(get_impala_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query)
                columns = [column[0] for column in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
    except ImpalaConnectionError:
        raise
    except Exception as exc:
        raise ImpalaQueryError(f"Impala query failed: {exc}") from exc

    result_rows = [dict(zip(columns, row)) for row in rows] if columns else []
    return {
        "columns": columns,
        "rows": result_rows,
    }


def run_scalar_query(query: str) -> Any:
    try:
        with closing(get_impala_connection()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
    except ImpalaConnectionError:
        raise
    except Exception as exc:
        raise ImpalaQueryError(f"Impala scalar query failed: {exc}") from exc

    if row is None:
        return None
    return row[0]


def check_impala_health() -> dict[str, Any]:
    result = run_scalar_query("SELECT 1")
    return {
        "status": "ok",
        "database": get_settings().impala_db,
        "result": result,
    }
