from __future__ import annotations

from typing import Any

from app.impala_client import execute_query
from app.config import settings

TABLE = f"{settings.db_name}.customer_dormant_segment"

# Business rules: reason code → recommended campaign action
REASON_TO_CAMPAIGN: dict[str, dict[str, str]] = {
    "MATURED_DEPOSIT": {
        "action": "Tawarkan renewal deposito atau tenor alternatif",
        "channel": "Relationship Manager / Phone Banking",
        "priority": "HIGH",
    },
    "LOW_TRANSACTION_COUNT": {
        "action": "Dorong penggunaan rekening sebagai rekening utama, bundling layanan transaksi",
        "channel": "Digital (Mobile Banking / Email) / Branch",
        "priority": "MEDIUM",
    },
    "NO_DIGITAL_ACTIVITY": {
        "action": "Onboarding digital — edukasi mobile banking, tawarkan cashback transaksi digital",
        "channel": "Branch / Telemarketing",
        "priority": "MEDIUM",
    },
    "LOW_BALANCE": {
        "action": "Tawarkan produk tabungan dengan setoran awal rendah atau program menabung rutin",
        "channel": "Digital / Branch",
        "priority": "LOW",
    },
    "NORMAL_ACTIVITY": {
        "action": "Maintain relationship — cross-sell produk sesuai segmen",
        "channel": "Digital / RM",
        "priority": "LOW",
    },
}


def get_campaign_recommendation(
    segment: str | None = None,
    dormant_reason_code: str | None = None,
    risk_level: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    MCP Tool: Get campaign recommendations for dormant customers.
    Returns top customers with recommended action based on dormant reason code.
    Optional filters: segment, dormant_reason_code, risk_level.
    """
    where_clauses = ["dormant_risk_level IN ('HIGH', 'MEDIUM')"]
    if segment:
        where_clauses.append(f"customer_segment = '{segment}'")
    if dormant_reason_code:
        where_clauses.append(f"dormant_reason_code = '{dormant_reason_code}'")
    if risk_level:
        where_clauses.append(f"dormant_risk_level = '{risk_level.upper()}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    sql = f"""
        SELECT
            customer_id,
            customer_segment,
            dormant_risk_level,
            dormant_reason_code,
            next_best_action,
            city,
            branch_name,
            total_deposit_balance,
            outstanding_loan_balance
        FROM {TABLE}
        {where_sql}
        ORDER BY
            CASE dormant_risk_level WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
            total_deposit_balance DESC
        LIMIT {limit}
    """

    try:
        result = execute_query(sql.strip())

        enriched_rows = []
        for row in result["rows"]:
            reason = row.get("dormant_reason_code") or "NORMAL_ACTIVITY"
            campaign_info = REASON_TO_CAMPAIGN.get(reason, REASON_TO_CAMPAIGN["NORMAL_ACTIVITY"])
            enriched_rows.append({**row, **campaign_info})

        return {
            "filters": {
                "segment": segment,
                "dormant_reason_code": dormant_reason_code,
                "risk_level": risk_level,
            },
            "columns": result["columns"] + ["action", "channel", "priority"],
            "rows": enriched_rows,
            "row_count": result["row_count"],
        }
    except Exception as exc:
        return {"error": str(exc)}


def get_campaign_summary_by_reason() -> dict[str, Any]:
    """
    MCP Tool: Aggregate campaign priority breakdown per dormant reason code.
    """
    sql = f"""
        SELECT
            dormant_reason_code,
            dormant_risk_level,
            COUNT(*) AS customer_count,
            ROUND(AVG(total_deposit_balance), 0) AS avg_deposit_balance
        FROM {TABLE}
        WHERE dormant_risk_level IN ('HIGH', 'MEDIUM')
        GROUP BY dormant_reason_code, dormant_risk_level
        ORDER BY customer_count DESC
    """

    try:
        result = execute_query(sql.strip())
        enriched = []
        for row in result["rows"]:
            reason = row.get("dormant_reason_code") or "NORMAL_ACTIVITY"
            campaign = REASON_TO_CAMPAIGN.get(reason, REASON_TO_CAMPAIGN["NORMAL_ACTIVITY"])
            enriched.append({**row, "recommended_action": campaign["action"], "channel": campaign["channel"]})

        return {
            "columns": result["columns"] + ["recommended_action", "channel"],
            "rows": enriched,
            "row_count": result["row_count"],
        }
    except Exception as exc:
        return {"error": str(exc)}
