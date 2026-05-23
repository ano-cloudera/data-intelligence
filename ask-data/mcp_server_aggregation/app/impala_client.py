from __future__ import annotations

import asyncio
import datetime
import threading
from contextlib import closing
from decimal import Decimal
from typing import Any

from impala.dbapi import connect

from app.config import settings

# ---------------------------------------------------------------------------
# Connection pool — reuse connections across tool calls
# ---------------------------------------------------------------------------

_pool: list[Any] = []
_pool_lock = threading.Lock()
_POOL_SIZE = 5


def _new_connection() -> Any:
    return connect(
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


def _get_connection() -> Any:
    with _pool_lock:
        if _pool:
            return _pool.pop()
    return _new_connection()


def _release_connection(conn: Any) -> None:
    with _pool_lock:
        if len(_pool) < _POOL_SIZE:
            _pool.append(conn)
            return
    try:
        conn.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Type safety
# ---------------------------------------------------------------------------

def _safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------

def _run_query(sql: str) -> dict[str, Any]:
    """Blocking Impala query using pooled connection."""
    conn = _get_connection()
    try:
        with closing(conn.cursor()) as cursor:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [
                {col: _safe(val) for col, val in zip(columns, row)}
                for row in cursor.fetchall()
            ]
            return {"columns": columns, "rows": rows, "row_count": len(rows)}
    except Exception:
        # Connection may be stale — discard it and don't return to pool
        try:
            conn.close()
        except Exception:
            pass
        raise
    else:
        _release_connection(conn)


def _run_query_safe(sql: str) -> dict[str, Any]:
    """Like _run_query but always returns connection to pool."""
    conn = _get_connection()
    ok = False
    try:
        with closing(conn.cursor()) as cursor:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [
                {col: _safe(val) for col, val in zip(columns, row)}
                for row in cursor.fetchall()
            ]
            ok = True
            return {"columns": columns, "rows": rows, "row_count": len(rows)}
    finally:
        if ok:
            _release_connection(conn)
        else:
            try:
                conn.close()
            except Exception:
                pass


def execute_query(sql: str) -> dict[str, Any]:
    return _run_query_safe(sql)


async def execute_query_async(sql: str) -> dict[str, Any]:
    return await asyncio.to_thread(_run_query_safe, sql)


def qualified_table() -> str:
    return f"{settings.db_name}.{settings.aggregation_table}"


def table_name() -> str:
    return settings.aggregation_table
