from __future__ import annotations

import re
from typing import Any

from app.impala_client import execute_query, qualified_table

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def run_sql_query(sql: str) -> dict[str, Any]:
    sql = sql.strip()
    if not sql.upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed."}
    if _FORBIDDEN.search(sql):
        return {"error": "Query contains forbidden operation."}

    table = qualified_table()
    if table.split(".")[-1] not in sql.lower():
        sql = sql.replace(
            "customer_aggregation",
            table,
            1,
        )
        if table not in sql:
            return {"error": f"Query must reference table: {table}"}

    try:
        return execute_query(sql)
    except Exception as exc:
        return {"error": str(exc)}
