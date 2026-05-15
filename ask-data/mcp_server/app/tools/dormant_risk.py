from __future__ import annotations

from typing import Any

from app.impala_client import execute_query
from app.config import settings

TABLE = f"{settings.db_name}.customer_dormant_segment"


def get_dormant_risk_summary(
    segment: str | None = None,
    branch_city: str | None = None,
    risk_level: str | None = None,
) -> dict[str, Any]:
    """
    MCP Tool: Summarize dormant risk distribution.
    Optional filters: segment, branch_city, risk_level (HIGH / MEDIUM / LOW / NONE).
    Returns count and percentage per dormant_risk_level.
    """
    where_clauses = []
    if segment:
        where_clauses.append(f"customer_segment = '{segment}'")
    if branch_city:
        where_clauses.append(f"branch_city = '{branch_city}'")
    if risk_level:
        where_clauses.append(f"dormant_risk_level = '{risk_level.upper()}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    sql = f"""
        SELECT
            dormant_risk_level,
            COUNT(*) AS customer_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
        FROM {TABLE}
        {where_sql}
        GROUP BY dormant_risk_level
        ORDER BY FIELD(dormant_risk_level, 'HIGH', 'MEDIUM', 'LOW', 'NONE')
    """

    try:
        result = execute_query(sql.strip())
        return {
            "filters": {
                "segment": segment,
                "branch_city": branch_city,
                "risk_level": risk_level,
            },
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
        }
    except Exception as exc:
        return {"error": str(exc)}


def get_dormant_reason_breakdown(
    segment: str | None = None,
    risk_level: str | None = None,
) -> dict[str, Any]:
    """
    MCP Tool: Breakdown dormant reason codes with count per segment or risk level.
    """
    where_clauses = ["dormant_reason_code IS NOT NULL"]
    if segment:
        where_clauses.append(f"customer_segment = '{segment}'")
    if risk_level:
        where_clauses.append(f"dormant_risk_level = '{risk_level.upper()}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    sql = f"""
        SELECT
            dormant_reason_code,
            COUNT(*) AS customer_count
        FROM {TABLE}
        {where_sql}
        GROUP BY dormant_reason_code
        ORDER BY customer_count DESC
    """

    try:
        result = execute_query(sql.strip())
        return {
            "filters": {"segment": segment, "risk_level": risk_level},
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
        }
    except Exception as exc:
        return {"error": str(exc)}
