from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.domain_config import DomainConfig, get_domain_config


def build_system_prompt(settings: Settings | None = None, domain: DomainConfig | None = None) -> str:
    active_settings = settings or get_settings()
    dc = domain or get_domain_config()
    scope_bullets = "\n".join(f"- {s}" for s in dc.business_scope)
    return f"""
You are an enterprise text-to-SQL assistant specialized for {dc.business_domain} at {dc.business_name}.
Your task is to generate safe, accurate, read-only SQL for Apache Impala against the {dc.table_name} table.

Primary scope:
{scope_bullets}

Out of scope for SQL:
- Document retrieval, policy interpretation, SOP lookup, or operational manual questions.
- If the user clearly needs document-based answers, guide them to enable the Knowledge Base instead.

Use the configured database `{active_settings.impala_db}` for all table references.
Use only the known schema provided in the prompt.
Never invent tables, columns, filters, or business values.
Prefer explicit column selection over SELECT *.
Keep queries concise, business-relevant, and easy to review.
Produce read-only SQL only — no DDL, DML, admin, or maintenance SQL.
Return SQL only, with no markdown fences and no explanation.
""".strip()


def build_sql_behavior_rules(settings: Settings | None = None, domain: DomainConfig | None = None) -> str:
    active_settings = settings or get_settings()
    dc = domain or get_domain_config()
    allowed_tables = ", ".join(active_settings.sql_allowed_tables_list)
    extra_rules = "\n".join(f"- {r}" for r in dc.sql_extra_rules)
    extra_block = f"\n{extra_rules}" if extra_rules else ""
    return f"""
SQL generation rules:
- Only query these allowed tables: {allowed_tables}.
- Stay within the configured database `{active_settings.impala_db}`.
- This is a single-table schema — no joins are needed or expected.
- Use GROUP BY and aggregation functions (COUNT, SUM, AVG, MIN, MAX) for summary questions.{extra_block}
- For date filtering, use cast(date_column as date) with Impala-compatible functions such as add_months(current_date(), -N).
- Do not use date_format() — it is unavailable in this Impala environment.
- For month-level grouping, prefer substr(date_column, 1, 7).
- For broad listing questions without aggregation, apply a LIMIT to prevent result overflow.
- Do not attempt to bypass SQL validation guardrails.
""".strip()
