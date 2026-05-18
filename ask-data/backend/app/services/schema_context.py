from __future__ import annotations

from app.core.domain_config import DomainConfig, get_domain_config


def build_database_description(domain: DomainConfig | None = None) -> str:
    dc = domain or get_domain_config()
    return (
        f"Database purpose: {dc.business_name} customer analytics platform. "
        f"Main use case: {dc.business_domain}."
    )


def build_table_descriptions(domain: DomainConfig | None = None) -> str:
    dc = domain or get_domain_config()
    col_lines = "\n".join(
        f"  - {col.name}: {col.description}" for col in dc.columns
    )
    return f"""
Table: {dc.full_table_name}
- Business meaning: {dc.table_description}
- Grain: {dc.table_grain}
- Columns:
{col_lines}
""".strip()


def build_relationship_guidance(domain: DomainConfig | None = None) -> str:
    dc = domain or get_domain_config()
    mapping_lines = "\n".join(
        f'  - "{m.term}" => {m.column}' for m in dc.term_mappings
    )
    mapping_block = f"\n- Business term mapping:\n{mapping_lines}" if mapping_lines else ""
    return f"""
Query guidance:
- Only query {dc.full_table_name}.
- Do not join to any other table.
- For business questions, prefer aggregate queries (COUNT, SUM, AVG, GROUP BY).
- For row-level or top-N queries, always include LIMIT 20.
- Never use SELECT *.
- Never expose PII columns. customer_id is allowed only as an analytics identifier.{mapping_block}
""".strip()


def build_schema_context(domain: DomainConfig | None = None) -> str:
    dc = domain or get_domain_config()
    return "\n\n".join(
        (
            build_database_description(dc),
            build_table_descriptions(dc),
            build_relationship_guidance(dc),
        )
    )
