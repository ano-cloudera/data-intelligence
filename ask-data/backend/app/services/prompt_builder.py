from __future__ import annotations

import os

from app.core.config import Settings, get_settings
from app.schemas.session import SessionMemoryState
from app.services.business_context import build_business_context
from app.services.schema_context import build_schema_context
from app.services.system_prompt import build_sql_behavior_rules, build_system_prompt
from app.services.token_budget import estimate_tokens, fits_budget


def build_memory_context(
    memory: SessionMemoryState | None,
    max_messages: int = 4,
    include_extras: bool = True,
) -> str:
    """include_extras controls last_intent/last_generated_sql/last_answer/
    last_result_preview — the other safe-to-drop-last layer when trimming
    for a token budget, since the conversation history line is usually
    the cheapest to cut and cuts first."""
    if memory is None:
        return ""

    sections: list[str] = []
    # max_messages <= 0 means "no history" — messages[-0:] would otherwise
    # slice the WHOLE list in Python, so guard it explicitly.
    recent_messages = memory.messages[-max_messages:] if max_messages > 0 else []
    if recent_messages:
        history_lines = [
            f"{message.role}: {message.content.strip()}"
            for message in recent_messages
            if message.content.strip()
        ]
        if history_lines:
            sections.append("Recent conversation:\n" + "\n".join(history_lines))

    if not include_extras:
        return "\n\n".join(sections)

    if memory.last_intent:
        sections.append(f"Last known user intent: {memory.last_intent}")

    if memory.last_generated_sql:
        sections.append(f"Last generated SQL:\n{memory.last_generated_sql}")

    if memory.last_answer:
        sections.append(f"Last assistant answer:\n{memory.last_answer}")

    if memory.last_result_preview and memory.last_result_preview.rows:
        sections.append(
            "Last result preview row count: "
            f"{memory.last_result_preview.row_count}"
        )

    return "\n\n".join(sections)


def build_composed_system_prompt(settings: Settings | None = None) -> str:
    active_settings = settings or get_settings()
    return "\n\n".join(
        (
            build_system_prompt(active_settings),
            build_sql_behavior_rules(active_settings),
            build_business_context(),
            build_schema_context(),
        )
    )


def build_prompt_debug_view(
    question: str,
    memory: SessionMemoryState | None = None,
    settings: Settings | None = None,
) -> dict[str, str]:
    messages = build_text_to_sql_messages(
        question=question,
        memory=memory,
        settings=settings,
    )
    return {
        "system_prompt": messages[0]["content"],
        "user_prompt": messages[1]["content"],
    }


def _build_sql_messages(
    question: str,
    system_prompt: str,
    memory_context: str,
) -> list[dict[str, str]]:
    user_prompt = f"""
Generate a single read-only SQL query for this question:
{question}
""".strip()

    if memory_context:
        user_prompt = (
            f"{memory_context}\n\n"
            "Generate a single read-only SQL query for the current question.\n"
            f"Current question:\n{question}"
        )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_text_to_sql_messages(
    question: str,
    memory: SessionMemoryState | None = None,
    settings: Settings | None = None,
) -> list[dict[str, str]]:
    active_settings = settings or get_settings()
    system_prompt = build_composed_system_prompt(active_settings)
    max_output_tokens = int(os.getenv("QWEN_MAX_TOKENS_SQL", "1024"))

    # Conversation history/extras are the only safe-to-shrink part of this
    # prompt (system prompt + schema context define correctness and must
    # not be trimmed). Try progressively less context — fewer recent
    # messages, then drop the last-intent/SQL/answer extras too, then no
    # memory context at all — until the estimated prompt fits the
    # server's context window with room left for the SQL output.
    trim_steps = [
        (4, True),
        (2, True),
        (1, True),
        (1, False),
        (0, False),
    ]
    for history_window, include_extras in trim_steps:
        memory_context = build_memory_context(
            memory, max_messages=history_window, include_extras=include_extras
        )
        messages = _build_sql_messages(question, system_prompt, memory_context)
        if fits_budget(messages, active_settings.qwen_max_model_len, max_output_tokens):
            return messages

    # Even with zero memory context the base prompt (system + schema)
    # alone exceeds the budget — that's a deployment misconfiguration
    # (schema too large for VLLM_MAX_MODEL_LEN), not something safe to
    # silently fix here. Return the smallest variant; the LLM call will
    # surface a clear error rather than us guessing what else to cut.
    return _build_sql_messages(question, system_prompt, "")
