from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.session import SessionMemoryState
from app.services.answer_prompt_builder import build_answer_messages
from app.services.chat_router import is_indonesian_text
from app.services.llm_router import LLMRouter
from llm.qwen_client import LLMChatResult


class AnswerGeneratorService:
    def __init__(
        self,
        llm_router: LLMRouter | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm_router = llm_router or LLMRouter(self.settings)

    def generate_answer(
        self,
        original_question: str,
        executed_sql: str,
        columns: list[str],
        rows: list[dict[str, Any]],
        row_count: int,
        truncated: bool,
        limit_applied: bool,
        memory: SessionMemoryState | None = None,
    ) -> LLMChatResult:
        if not rows:
            if is_indonesian_text(original_question):
                fallback = "Tidak ada data yang cocok untuk pertanyaan ini pada hasil saat ini."
            else:
                fallback = "No matching records were found for this request in the current data."
            return LLMChatResult(content=fallback, reasoning=None)

        # Proactive cap: only send up to llm_max_rows_for_narration rows to
        # the LLM regardless of context window size — the model doesn't
        # need to see every row to produce a correct, grounded narrative,
        # and capping here keeps prompts small and predictable by default.
        # build_answer_messages' own token-budget trim is only a reactive
        # safety net for whatever still doesn't fit after this cap.
        narration_cap = self.settings.llm_max_rows_for_narration
        rows_for_narration = rows[:narration_cap] if len(rows) > narration_cap else rows
        capped_for_narration = len(rows_for_narration) < len(rows)
        # If we capped, the answer must still reflect the true row_count —
        # never let the model think fewer rows exist than actually matched.
        effective_truncated = truncated or capped_for_narration

        messages = build_answer_messages(
            original_question=original_question,
            executed_sql=executed_sql,
            columns=columns,
            rows=rows_for_narration,
            row_count=row_count,
            truncated=effective_truncated,
            limit_applied=limit_applied,
            rows_already_capped=capped_for_narration,
        )
        result = self.llm_router.get_client(memory).chat(messages=messages, temperature=0.2)
        answer = result.content

        if effective_truncated and "preview" not in answer.lower():
            suffix = (
                " Hanya preview data yang ditampilkan di sini."
                if is_indonesian_text(original_question)
                else " Only a preview of the matching records is shown here."
            )
            answer = f"{answer}{suffix}"

        return LLMChatResult(content=answer.strip(), reasoning=result.reasoning)
