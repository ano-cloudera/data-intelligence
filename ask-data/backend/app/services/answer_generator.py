from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.session import SessionMemoryState
from app.services.answer_prompt_builder import build_answer_messages
from app.services.chat_router import is_indonesian_text
from app.services.llm_router import LLMRouter


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
    ) -> str:
        if not rows:
            if is_indonesian_text(original_question):
                return "Tidak ada data yang cocok untuk pertanyaan ini pada hasil saat ini."
            return "No matching records were found for this request in the current data."

        messages = build_answer_messages(
            original_question=original_question,
            executed_sql=executed_sql,
            columns=columns,
            rows=rows,
            row_count=row_count,
            truncated=truncated,
            limit_applied=limit_applied,
        )
        answer = self.llm_router.get_client(memory).chat(messages=messages, temperature=0.2)

        if truncated and "preview" not in answer.lower():
            suffix = (
                " Hanya preview data yang ditampilkan di sini."
                if is_indonesian_text(original_question)
                else " Only a preview of the matching records is shown here."
            )
            answer = f"{answer}{suffix}"

        return answer.strip()
