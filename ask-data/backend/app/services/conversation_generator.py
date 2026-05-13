from __future__ import annotations

from app.core.config import Settings, get_settings
from app.schemas.session import SessionMemoryState
from app.services.chat_router import (
    build_acknowledgement_answer,
    build_farewell_answer,
    build_greeting_answer,
    build_out_of_scope_answer,
    is_acknowledgement,
    is_farewell,
    is_greeting_or_smalltalk,
)
from app.services.conversation_prompt_builder import build_conversation_messages
from app.services.llm_client import LLMClientError
from app.services.llm_router import LLMRouter


class ConversationGeneratorService:
    def __init__(
        self,
        llm_router: LLMRouter | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm_router = llm_router or LLMRouter(self.settings)

    def generate_response(
        self,
        question: str,
        memory: SessionMemoryState | None = None,
    ) -> str:
        recent_question = None
        recent_answer = None
        if memory and memory.messages:
            for message in reversed(memory.messages):
                if message.role == "assistant" and recent_answer is None:
                    recent_answer = message.content
                elif message.role == "user" and recent_question is None:
                    recent_question = message.content
                if recent_question and recent_answer:
                    break

        messages = build_conversation_messages(
            question=question,
            recent_answer=recent_answer,
            recent_question=recent_question,
        )

        try:
            return self.llm_router.get_client(memory).chat(messages=messages, temperature=0.6)
        except LLMClientError:
            return self._fallback_response(question)

    @staticmethod
    def _fallback_response(question: str) -> str:
        if is_greeting_or_smalltalk(question):
            return build_greeting_answer(question)
        if is_acknowledgement(question):
            return build_acknowledgement_answer(question)
        if is_farewell(question):
            return build_farewell_answer(question)
        return build_out_of_scope_answer(question)
