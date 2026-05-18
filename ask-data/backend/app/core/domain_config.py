from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any


@dataclass
class ColumnDef:
    name: str
    description: str


@dataclass
class TermMapping:
    term: str
    column: str


@dataclass
class DomainConfig:
    business_name: str
    business_domain: str
    database_name: str
    table_name: str
    table_description: str
    table_grain: str
    business_scope: list[str]
    columns: list[ColumnDef]
    term_mappings: list[TermMapping]
    example_questions: list[str]
    sql_extra_rules: list[str]
    guardrail_out_of_scope_en: str
    guardrail_out_of_scope_id: str
    ambiguity_guidance: list[str]

    @property
    def full_table_name(self) -> str:
        return f"{self.database_name}.{self.table_name}"


_DEFAULTS: dict[str, Any] = {
    "business_name": "Enterprise",
    "business_domain": "data analytics",
    "database_name": "default",
    "table_name": "main_table",
    "table_description": "Main analytics table",
    "table_grain": "one row per record",
    "business_scope": ["Data analytics and reporting."],
    "columns": [],
    "term_mappings": [],
    "example_questions": ["Show total records by category."],
    "sql_extra_rules": [],
    "guardrail_out_of_scope_en": (
        "This assistant is focused on data analytics for this domain. "
        "Please ask questions related to the available dataset."
    ),
    "guardrail_out_of_scope_id": (
        "Asisten ini difokuskan pada analitik data untuk domain ini. "
        "Silakan ajukan pertanyaan terkait dataset yang tersedia."
    ),
    "ambiguity_guidance": [
        "All data is in the main table — no joins are needed.",
        "If a question is broad, return a practical preview query with LIMIT applied.",
    ],
}


def _find_config_file() -> Path | None:
    """Search for domain_config.yaml relative to this file or CWD."""
    candidates = [
        Path(__file__).parent.parent.parent / "domain_config.yaml",
        Path.cwd() / "domain_config.yaml",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _load_raw() -> dict[str, Any]:
    config_path = _find_config_file()
    if config_path is None:
        return {}
    try:
        import yaml  # type: ignore
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except ImportError:
        # yaml not available — fall through to defaults
        return {}
    except Exception:
        return {}


@lru_cache(maxsize=1)
def get_domain_config() -> DomainConfig:
    raw = _load_raw()

    def get(key: str) -> Any:
        return raw.get(key, _DEFAULTS[key])

    raw_columns = get("columns")
    columns = [
        ColumnDef(name=c["name"], description=c.get("description", ""))
        for c in raw_columns
        if isinstance(c, dict) and c.get("name")
    ]

    raw_mappings = get("term_mappings")
    term_mappings = [
        TermMapping(term=m["term"], column=m["column"])
        for m in raw_mappings
        if isinstance(m, dict) and m.get("term") and m.get("column")
    ]

    return DomainConfig(
        business_name=str(get("business_name")),
        business_domain=str(get("business_domain")),
        database_name=str(get("database_name")),
        table_name=str(get("table_name")),
        table_description=str(get("table_description")),
        table_grain=str(get("table_grain")),
        business_scope=[str(s) for s in get("business_scope")],
        columns=columns,
        term_mappings=term_mappings,
        example_questions=[str(q) for q in get("example_questions")],
        sql_extra_rules=[str(r) for r in get("sql_extra_rules")],
        guardrail_out_of_scope_en=str(get("guardrail_out_of_scope_en")).strip(),
        guardrail_out_of_scope_id=str(get("guardrail_out_of_scope_id")).strip(),
        ambiguity_guidance=[str(g) for g in get("ambiguity_guidance")],
    )
