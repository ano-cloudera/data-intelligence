from __future__ import annotations

import re
from typing import Any

from app.impala_client import execute_query
from app.config import settings

_ALLOWED_PATTERN = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def run_sql_query(sql: str) -> dict[str, Any]:
    """
    MCP Tool: Execute a raw SELECT query against customer_dormant_segment.
    Only SELECT queries are allowed.
    """
    sql_clean = sql.strip().rstrip(";")

    if not _ALLOWED_PATTERN.match(sql_clean):
        return {"error": "Only SELECT queries are allowed."}
    if _FORBIDDEN.search(sql_clean):
        return {"error": "Query contains forbidden SQL operations."}
    if settings.db_name.lower() not in sql_clean.lower():
        sql_clean = sql_clean.replace(
            "customer_dormant_segment",
            f"{settings.db_name}.customer_dormant_segment",
        )

    try:
        result = execute_query(sql_clean)
        return {
            "sql": sql_clean,
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
        }
    except Exception as exc:
        return {"error": str(exc)}
