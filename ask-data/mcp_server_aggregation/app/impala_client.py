from __future__ import annotations

import asyncio
import datetime
from contextlib import closing
from decimal import Decimal
from typing import Any

from impala.dbapi import connect

from app.config import settings


def _safe(value: Any) -> Any:
    """Convert non-JSON-serializable Impala types to plain Python types."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


def _run_query(sql: str) -> dict[str, Any]:
    """Blocking Impala query — run via asyncio.to_thread to avoid blocking event loop."""
    conn = connect(
        host=settings.impala_host,
        port=settings.impala_port,
        database=settings.db_name,
        user=settings.cdp_user,
        password=settings.cdp_pass,
        use_ssl=True,
        auth_mechanism="PLAIN",
        http_path=settings.impala_http_path,
        use_http_transport=True,
    )
    with closing(conn):
        with closing(conn.cursor()) as cursor:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [
                {col: _safe(val) for col, val in zip(columns, row)}
                for row in cursor.fetchall()
            ]
            return {"columns": columns, "rows": rows, "row_count": len(rows)}


def execute_query(sql: str) -> dict[str, Any]:
    """Sync wrapper — dipanggil dari tool functions (non-async context)."""
    return _run_query(sql)


async def execute_query_async(sql: str) -> dict[str, Any]:
    """Async wrapper — jalankan query di thread pool agar event loop tidak terblok."""
    return await asyncio.to_thread(_run_query, sql)


def qualified_table() -> str:
    return f"{settings.db_name}.{settings.aggregation_table}"


def table_name() -> str:
    return settings.aggregation_table
