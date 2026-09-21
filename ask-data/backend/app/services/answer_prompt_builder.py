from __future__ import annotations

import json
import os
from typing import Any

from app.core.config import get_settings
from app.services.answer_system_prompt import build_answer_system_prompt
from app.services.token_budget import fits_budget


def _build_messages(
    system_prompt: str,
    original_question: str,
    executed_sql: str,
    result_payload: dict[str, Any],
    row_preview_truncated_for_prompt: bool,
) -> list[dict[str, str]]:
    preview_note = (
        "\n(Note: only a sample of the matching rows is shown above to fit "
        "the model's context window — row_count above is still the true total.)"
        if row_preview_truncated_for_prompt
        else ""
    )
    user_prompt = f"""
Original business question:
{original_question}

Executed SQL:
{executed_sql}

Result preview JSON:
{json.dumps(result_payload, ensure_ascii=True, default=str)}{preview_note}

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
    max_output_tokens = int(os.getenv("QWEN_MAX_TOKENS_ANSWER", "1200"))
    max_model_len = get_settings().qwen_max_model_len

    # The row preview is the only safe-to-shrink part of this prompt — the
    # question, SQL, and system prompt define correctness and must stay
    # intact. If the full row set doesn't fit the server's context window,
    # progressively send fewer rows (never fewer than 1, so the model
    # still has real data to ground its answer in) rather than letting a
    # raw BadRequestError reach the user.
    for row_slice in (len(rows), 50, 20, 10, 5, 1):
        sliced_rows = rows[:row_slice] if row_slice < len(rows) else rows
        result_payload = {
            "columns": columns,
            "rows": sliced_rows,
            "row_count": row_count,
            "truncated": truncated,
            "limit_applied": limit_applied,
        }
        row_preview_truncated_for_prompt = len(sliced_rows) < len(rows)
        messages = _build_messages(
            system_prompt,
            original_question,
            executed_sql,
            result_payload,
            row_preview_truncated_for_prompt,
        )
        if fits_budget(messages, max_model_len, max_output_tokens):
            return messages
        if not sliced_rows:
            break

    # Even a single-row preview exceeds the budget (e.g. very wide rows) —
    # return it anyway; the LLM call will surface a clear error rather
    # than us guessing what else to cut.
    return messages
