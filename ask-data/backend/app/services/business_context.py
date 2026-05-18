from __future__ import annotations

from app.core.domain_config import DomainConfig, get_domain_config


def build_supported_question_examples(domain: DomainConfig | None = None) -> str:
    dc = domain or get_domain_config()
    lines = "\n".join(f"- {q}" for q in dc.example_questions)
    return f"Supported business question patterns include:\n{lines}"


def build_ambiguity_guidance(domain: DomainConfig | None = None) -> str:
    dc = domain or get_domain_config()
    lines = "\n".join(f"- {g}" for g in dc.ambiguity_guidance)
    return f"Interpretation guidance:\n- Prefer the safest reasonable interpretation of ambiguous questions.\n- Do not invent values that are not present in the schema.\n- Use grouping and aggregation for summary questions.\n{lines}"


def build_business_context(domain: DomainConfig | None = None) -> str:
    dc = domain or get_domain_config()
    header = (
        f"Business context: The dataset is the {dc.table_name} table — "
        f"a single-table view of {dc.business_name} customers enriched with {dc.business_domain}."
    )
    return "\n\n".join(
        (
            header,
            build_supported_question_examples(dc),
            build_ambiguity_guidance(dc),
        )
    )
