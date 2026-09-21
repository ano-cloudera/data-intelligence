import json
import os
import sqlite3
from datetime import datetime
from typing import Iterable

from mcp.server.fastmcp import FastMCP

DB_PATH = os.environ.get(
    "BPJS_SQLITE_DB",
    ""
)

LOG_FILE = os.path.join(os.path.dirname(__file__), "mcp_sqlite.log")

mcp = FastMCP("bpjs-sqlite")

VALID_CLAIM_STATUS = {
    "Pending Verifikasi",
    "Dalam Review",
    "Eskalasi",
    "Selesai",
    "Ditolak",
}

VALID_QUEUE_STATUS = {
    "Open",
    "In Progress",
    "Waiting Clarification",
    "Escalated",
    "Closed",
}

VALID_REFERRAL_STATUS = {
    "Open",
    "Waiting Clarification",
    "Approved",
    "Rejected",
    "Completed",
}

VALID_FLAG_STATUS = {
    "Open",
    "Resolved",
    "Pending",
}


def log(msg: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")


def get_conn() -> sqlite3.Connection:
    if not DB_PATH:
        raise ValueError("BPJS_SQLITE_DB is not set.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_str(value: str) -> str:
    return value.strip()


def validate_int(value: int, min_value: int, max_value: int, field_name: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{field_name} harus berupa integer.")
    if value < min_value or value > max_value:
        raise ValueError(f"{field_name} harus antara {min_value} dan {max_value}.")
    return value


def validate_choice(value: str, valid_values: Iterable[str], field_name: str) -> str:
    value = normalize_str(value)
    valid_map = {v.lower(): v for v in valid_values}
    if value.lower() not in valid_map:
        allowed = ", ".join(sorted(valid_values))
        raise ValueError(f"{field_name} tidak valid. Pilihan yang diizinkan: {allowed}")
    return valid_map[value.lower()]


def rows_to_text(rows: list[sqlite3.Row]) -> str:
    if not rows:
        return "Tidak ada data."
    return json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2)


def run_query(sql: str, params: tuple = ()) -> str:
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return rows_to_text(rows)


@mcp.tool()
def health_check() -> str:
    """Check whether the BPJS operational data tool is running."""
    log("Tool called: health_check")
    return "BPJS operational data tool is running."


@mcp.tool()
def get_claim_status_summary() -> str:
    """Return jumlah kasus per status dari data operasional klaim."""
    log("Tool called: get_claim_status_summary")
    sql = """
    SELECT status, COUNT(*) AS total_cases
    FROM claim_cases
    GROUP BY status
    ORDER BY total_cases DESC
    """
    return run_query(sql)


@mcp.tool()
def get_overdue_review_cases() -> str:
    """Return 10 kasus review yang overdue lebih dari 3 hari."""
    log("Tool called: get_overdue_review_cases")
    sql = """
    SELECT case_id, queue_status, assigned_reviewer, overdue_days, next_action
    FROM review_queue
    WHERE overdue_days > 3
    ORDER BY overdue_days DESC
    LIMIT 10
    """
    return run_query(sql)


@mcp.tool()
def search_case_by_id(case_id: str) -> str:
    """Return detail satu kasus berdasarkan case ID, misalnya KR-2026-014."""
    case_id = normalize_str(case_id)
    log(f"Tool called: search_case_by_id case_id={case_id}")
    sql = """
    SELECT case_id, participant_id, participant_name, region, provider_type,
           facility_name, claim_type, diagnosis_group, claim_amount, status,
           priority_level, anomaly_score, suspected_issue, owner_unit
    FROM claim_cases
    WHERE case_id = ?
    """
    return run_query(sql, (case_id,))


@mcp.tool()
def get_claims_by_status(status: str) -> str:
    """Return daftar kasus klaim berdasarkan status, misalnya Pending Verifikasi atau Eskalasi."""
    status = validate_choice(status, VALID_CLAIM_STATUS, "status")
    log(f"Tool called: get_claims_by_status status={status}")
    sql = """
    SELECT case_id, participant_name, claim_amount, status, priority_level, owner_unit
    FROM claim_cases
    WHERE status = ?
    ORDER BY claim_amount DESC
    LIMIT 20
    """
    return run_query(sql, (status,))


@mcp.tool()
def get_cases_by_reviewer(reviewer_name: str) -> str:
    """Return daftar kasus review yang sedang ditangani reviewer tertentu."""
    reviewer_name = normalize_str(reviewer_name)
    log(f"Tool called: get_cases_by_reviewer reviewer_name={reviewer_name}")
    sql = """
    SELECT case_id, queue_status, assigned_reviewer, overdue_days, next_action, escalation_level
    FROM review_queue
    WHERE lower(assigned_reviewer) = lower(?)
    ORDER BY overdue_days DESC
    LIMIT 20
    """
    return run_query(sql, (reviewer_name,))


@mcp.tool()
def get_review_cases_by_status(queue_status: str) -> str:
    """Return daftar kasus review berdasarkan queue status, misalnya Open atau Waiting Clarification."""
    queue_status = validate_choice(queue_status, VALID_QUEUE_STATUS, "queue_status")
    log(f"Tool called: get_review_cases_by_status queue_status={queue_status}")
    sql = """
    SELECT case_id, queue_status, assigned_reviewer, overdue_days, next_action
    FROM review_queue
    WHERE queue_status = ?
    ORDER BY overdue_days DESC
    LIMIT 20
    """
    return run_query(sql, (queue_status,))


@mcp.tool()
def get_overdue_cases_min_days(min_days: int) -> str:
    """Return kasus review yang overdue lebih dari jumlah hari tertentu."""
    min_days = validate_int(min_days, 1, 365, "min_days")
    log(f"Tool called: get_overdue_cases_min_days min_days={min_days}")
    sql = """
    SELECT case_id, queue_status, assigned_reviewer, overdue_days, next_action
    FROM review_queue
    WHERE overdue_days > ?
    ORDER BY overdue_days DESC
    LIMIT 20
    """
    return run_query(sql, (min_days,))


@mcp.tool()
def get_top_priority_claims() -> str:
    """Return top 5 klaim prioritas aktif dengan nilai klaim tertinggi."""
    log("Tool called: get_top_priority_claims")
    sql = """
    SELECT case_id, participant_name, claim_amount, status, priority_level, anomaly_score
    FROM claim_cases
    WHERE status IN ('Pending Verifikasi', 'Dalam Review', 'Eskalasi')
    ORDER BY claim_amount DESC
    LIMIT 5
    """
    return run_query(sql)


@mcp.tool()
def get_referral_cases_by_status(referral_status: str) -> str:
    """Return daftar referral berdasarkan status, misalnya Waiting Clarification."""
    referral_status = validate_choice(referral_status, VALID_REFERRAL_STATUS, "referral_status")
    log(f"Tool called: get_referral_cases_by_status referral_status={referral_status}")
    sql = """
    SELECT referral_id, participant_id, referral_source, referral_target,
           referral_reason, referral_status, clarification_needed, owner_unit
    FROM referral_cases
    WHERE referral_status = ?
    ORDER BY referral_date DESC
    LIMIT 20
    """
    return run_query(sql, (referral_status,))


@mcp.tool()
def get_referral_clarification_cases() -> str:
    """Return daftar referral yang masih membutuhkan klarifikasi."""
    log("Tool called: get_referral_clarification_cases")
    sql = """
    SELECT referral_id, participant_id, referral_target, referral_status, owner_unit
    FROM referral_cases
    WHERE clarification_needed = 1
    ORDER BY referral_date DESC
    LIMIT 10
    """
    return run_query(sql)


@mcp.tool()
def get_participant_flags(flag_status: str) -> str:
    """Return daftar flag administrasi peserta berdasarkan status flag."""
    flag_status = validate_choice(flag_status, VALID_FLAG_STATUS, "flag_status")
    log(f"Tool called: get_participant_flags flag_status={flag_status}")
    sql = """
    SELECT flag_id, participant_id, participant_name, flag_type, flag_status, related_case_id, owner_unit
    FROM participant_admin_flags
    WHERE flag_status = ?
    ORDER BY participant_name
    LIMIT 20
    """
    return run_query(sql, (flag_status,))


@mcp.tool()
def get_cases_summary_by_region(region: str) -> str:
    """Return ringkasan jumlah kasus dan total nilai klaim untuk satu region."""
    region = normalize_str(region)
    log(f"Tool called: get_cases_summary_by_region region={region}")
    sql = """
    SELECT region, status, COUNT(*) AS total_cases, ROUND(SUM(claim_amount), 2) AS total_claim_amount
    FROM claim_cases
    WHERE lower(region) = lower(?)
    GROUP BY region, status
    ORDER BY total_cases DESC
    """
    return run_query(sql, (region,))


@mcp.tool()
def get_reviewer_workload_summary() -> str:
    """Return summary workload reviewer berdasarkan total kasus, overdue cases, dan escalated cases."""
    log("Tool called: get_reviewer_workload_summary")
    sql = """
    SELECT
      assigned_reviewer,
      COUNT(*) AS total_cases,
      SUM(CASE WHEN overdue_days > 3 THEN 1 ELSE 0 END) AS overdue_cases,
      SUM(CASE WHEN queue_status = 'Escalated' THEN 1 ELSE 0 END) AS escalated_cases
    FROM review_queue
    GROUP BY assigned_reviewer
    ORDER BY overdue_cases DESC, total_cases DESC
    LIMIT 10
    """
    return run_query(sql)


@mcp.tool()
def get_high_risk_overdue_cases() -> str:
    """Return high risk overdue cases berdasarkan overdue review dan anomaly score."""
    log("Tool called: get_high_risk_overdue_cases")
    sql = """
    SELECT
      c.case_id,
      c.participant_name,
      c.claim_amount,
      c.status,
      c.anomaly_score,
      r.assigned_reviewer,
      r.overdue_days,
      r.next_action
    FROM claim_cases c
    JOIN review_queue r
      ON c.case_id = r.case_id
    WHERE r.overdue_days > 7
      AND c.status IN ('Dalam Review', 'Eskalasi')
    ORDER BY c.anomaly_score DESC, r.overdue_days DESC
    LIMIT 10
    """
    return run_query(sql)


if __name__ == "__main__":
    log("Starting SQLite MCP server")
    mcp.run()