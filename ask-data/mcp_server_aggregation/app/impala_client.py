from __future__ import annotations

from contextlib import closing
from typing import Any

from impala.dbapi import connect

from app.config import settings

TABLE = "customer_aggregation"


def execute_query(sql: str) -> dict[str, Any]:
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
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return {"columns": columns, "rows": rows, "row_count": len(rows)}


def qualified_table() -> str:
    return f"{settings.db_name}.{TABLE}"
