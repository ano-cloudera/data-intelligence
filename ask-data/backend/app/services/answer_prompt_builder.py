from __future__ import annotations

import json
from typing import Any

from app.services.answer_system_prompt import build_answer_system_prompt


def build_answer_messages(
    original_question: str,
    executed_sql: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    row_count: int,
    truncated: bool,
    limit_applied: bool,
) -> list[dict[str, str]]:
    system_prompt = build_answer_system_prompt()
    result_payload = {
        "columns": columns,
        "rows": rows,
        "row_count": row_count,
        "truncated": truncated,
        "limit_applied": limit_applied,
    }
    user_prompt = f"""
Original business question:
{original_question}

Executed SQL:
{executed_sql}

Result preview JSON:
{json.dumps(result_payload, ensure_ascii=True, default=str)}

Write one concise, natural, business-friendly answer grounded only in this result.
Lead with the key takeaway.
CRITICAL: Respond ENTIRELY in the same language as the original business question. If the question is in Bahasa Indonesia, your entire answer MUST be in Bahasa Indonesia. If the question is in English, answer entirely in English. Do not mix languages.
If no rows are present, say that no matching records were found.
If truncation is true, mention that only a preview is shown.
Do not invent any unsupported interpretation.
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
