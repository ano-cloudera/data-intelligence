from __future__ import annotations

from typing import Any

from impala.dbapi import connect

from app.config import settings


def _get_connection():
    return connect(
        host=settings.impala_host,
        port=settings.impala_port,
        http_path=settings.impala_http_path,
        auth_mechanism="LDAP",
        user=settings.cdp_user,
        password=settings.cdp_pass,
        use_ssl=True,
    )


def execute_query(sql: str) -> dict[str, Any]:
    """Execute a SELECT query and return columns + rows."""
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description or []]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return {"columns": columns, "rows": rows, "row_count": len(rows)}
    finally:
        conn.close()
