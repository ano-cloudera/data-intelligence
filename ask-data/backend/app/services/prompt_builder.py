from __future__ import annotations

from app.core.config import Settings, get_settings
from app.schemas.session import SessionMemoryState
from app.services.business_context import build_business_context
from app.services.schema_context import build_schema_context
from app.services.system_prompt import build_sql_behavior_rules, build_system_prompt


def build_memory_context(memory: SessionMemoryState | None, max_messages: int = 4) -> str:
    if memory is None:
        return ""

    sections: list[str] = []
    recent_messages = memory.messages[-max_messages:]
    if recent_messages:
        history_lines = [
            f"{message.role}: {message.content.strip()}"
            for message in recent_messages
            if message.content.strip()
        ]
        if history_lines:
            sections.append("Recent conversation:\n" + "\n".join(history_lines))

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


def build_text_to_sql_messages(
    question: str,
    memory: SessionMemoryState | None = None,
    settings: Settings | None = None,
) -> list[dict[str, str]]:
    active_settings = settings or get_settings()
    memory_context = build_memory_context(memory)
    system_prompt = build_composed_system_prompt(active_settings)

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
