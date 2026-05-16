from __future__ import annotations

import re

from app.core.config import Settings, get_settings

FORBIDDEN_PATTERNS = (
    r"\binsert\b",
    r"\bupdate\b",
    r"\bdelete\b",
    r"\bdrop\b",
    r"\balter\b",
    r"\btruncate\b",
    r"\bcreate\b",
    r"\bmerge\b",
    r"\bupsert\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\binvalidate\b",
    r"\brefresh\b",
    r"\bcompute\b",
    r"\bexplain\b",
    r"\bdescribe\s+formatted\b",
    r"\bdate_format\s*\(",
)


class SQLValidationError(ValueError):
    """Raised when SQL fails validation."""


def strip_markdown_fences(sql: str) -> str:
    text = sql.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return text


def normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", strip_markdown_fences(sql)).strip()


def reject_empty_sql(sql: str) -> None:
    if not sql.strip():
        raise SQLValidationError("SQL must not be empty.")


def reject_multi_statement_sql(sql: str) -> None:
    trimmed = sql.strip()
    if ";" in trimmed[:-1]:
        raise SQLValidationError("Multiple SQL statements are not allowed.")
    if trimmed.endswith(";"):
        trimmed = trimmed[:-1].strip()
    if ";" in trimmed:
        raise SQLValidationError("Multiple SQL statements are not allowed.")


def reject_forbidden_keywords(sql: str) -> None:
    lowered = sql.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, lowered):
            raise SQLValidationError("SQL contains a forbidden keyword or statement.")


def ensure_read_only_query(sql: str) -> None:
    lowered = sql.lower().lstrip()
    if lowered.startswith("select "):
        return
    if lowered.startswith("with "):
        if re.search(r"\)\s*select\b", lowered):
            return
    raise SQLValidationError("Only SELECT queries are allowed.")


def extract_cte_names(sql: str) -> set[str]:
    return {match.group(1).lower() for match in re.finditer(r"\bwith\s+([a-zA-Z_][\w]*)\s+as\b", sql, flags=re.IGNORECASE)} | {
        match.group(1).lower() for match in re.finditer(r",\s*([a-zA-Z_][\w]*)\s+as\b", sql, flags=re.IGNORECASE)
    }


def extract_table_references(sql: str) -> list[str]:
    matches = re.findall(r"\b(?:from|join)\s+([a-zA-Z_][\w\.]*)", sql, flags=re.IGNORECASE)
    return [match.lower() for match in matches]


def validate_allowed_tables(
    sql: str,
    settings: Settings | None = None,
    session_locked_table: str | None = None,
) -> None:
    active_settings = settings or get_settings()
    cte_names = extract_cte_names(sql)
    if session_locked_table:
        allowed_tables = {session_locked_table.strip().lower()}
    else:
        allowed_tables = set(active_settings.sql_allowed_tables_list)
    qualified_allowed_tables = {
        f"{active_settings.impala_db.lower()}.{table}" for table in allowed_tables
    }

    for table_ref in extract_table_references(sql):
        if table_ref in cte_names:
            continue
        if table_ref in allowed_tables or table_ref in qualified_allowed_tables:
            continue
        raise SQLValidationError(f"Table access is not allowed: {table_ref}")


def has_limit(sql: str) -> bool:
    return bool(re.search(r"\blimit\s+\d+\b", sql, flags=re.IGNORECASE))


def is_broad_listing_query(sql: str) -> bool:
    lowered = sql.lower()
    aggregate_markers = (" count(", " sum(", " avg(", " min(", " max(", " group by ", " distinct ")
    return not any(marker in lowered for marker in aggregate_markers)


def apply_default_limit(sql: str, settings: Settings | None = None) -> tuple[str, bool]:
    active_settings = settings or get_settings()
    if has_limit(sql) or not is_broad_listing_query(sql):
        return sql, False
    return f"{sql} LIMIT {active_settings.sql_default_limit}", True


def validate_and_prepare_sql(
    sql: str,
    settings: Settings | None = None,
    session_locked_table: str | None = None,
) -> tuple[str, bool]:
    active_settings = settings or get_settings()
    cleaned_sql = normalize_sql(sql)
    reject_empty_sql(cleaned_sql)
    reject_multi_statement_sql(cleaned_sql)
    if cleaned_sql.endswith(";"):
        cleaned_sql = cleaned_sql[:-1].strip()
    reject_forbidden_keywords(cleaned_sql)
    ensure_read_only_query(cleaned_sql)
    validate_allowed_tables(cleaned_sql, active_settings, session_locked_table=session_locked_table)
    return apply_default_limit(cleaned_sql, active_settings)
