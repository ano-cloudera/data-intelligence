from __future__ import annotations

import re
from typing import Any

from app.impala_client import execute_query, qualified_table, table_name

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def run_sql_query(sql: str) -> dict[str, Any]:
    sql = sql.strip().rstrip(";")
    if not sql.upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed."}
    if _FORBIDDEN.search(sql):
        return {"error": "Query contains forbidden operation."}

    full_table = qualified_table()
    short_table = table_name()

    # Qualify unqualified table reference so the correct db/table is always used
    sql_lower = sql.lower()
    if short_table not in sql_lower and full_table not in sql_lower:
        return {"error": f"Query must reference table: {short_table}"}
    if short_table in sql_lower and full_table not in sql_lower:
        sql = re.sub(
            rf"\b{re.escape(short_table)}\b",
            full_table,
            sql,
            flags=re.IGNORECASE,
        )

    try:
        result = execute_query(sql)
        return {
            "sql": sql,
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
        }
    except Exception as exc:
        return {"error": str(exc)}
