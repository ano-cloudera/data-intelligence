"""
Local Qwen client for existing Ask Data backend.

Integration target:
- Replace Azure OpenAI / Bedrock calls with this client.
- vLLM exposes OpenAI-compatible /v1/chat/completions.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

# Safety net only: some OpenAI-compatible servers inline the reasoning as a
# <think>...</think> block inside message.content instead of the separate
# `reasoning`/`reasoning_content` field. If that happens we still split it
# out structurally (not by scrubbing the visible answer with a blind regex
# over the final text) so callers never see reasoning mixed into content.
_THINK_BLOCK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)


def _is_thinking_enabled() -> bool:
    """Application-level toggle for Qwen3 / Qwen3.5 reasoning mode.

    VLLM_ENABLE_THINKING is OUR config flag, not a native vLLM/OpenAI env
    var — the backend is responsible for translating it into the request
    parameter vLLM actually understands:
        extra_body["chat_template_kwargs"]["enable_thinking"]
    """
    return os.getenv("VLLM_ENABLE_THINKING", "false").strip().lower() == "true"


@dataclass
class LLMChatResult:
    """Structured chat result: final answer and (optional) reasoning kept
    as separate fields from the moment the LLM response is parsed, never
    concatenated into one string."""

    content: str
    reasoning: str | None = None


class QwenClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("QWEN_BASE_URL", "http://localhost:8000/v1")
        self.api_key = os.getenv("QWEN_API_KEY", "bjt-local-vllm")
        self.model = os.getenv("QWEN_MODEL", "Qwen/Qwen3-8B-AWQ")
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        self.thinking_enabled = _is_thinking_enabled()

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
        extra_body: Optional[Dict[str, Any]] = None,
    ) -> LLMChatResult:
        merged_extra_body: Dict[str, Any] = {
            "chat_template_kwargs": {"enable_thinking": self.thinking_enabled},
        }
        if extra_body:
            merged_extra_body.update(extra_body)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=merged_extra_body,
        )
        message = response.choices[0].message
        content = message.content or ""

        # Preferred path: OpenAI-compatible reasoning field, kept separate
        # from content from the start (no string surgery needed).
        reasoning = getattr(message, "reasoning_content", None) or getattr(
            message, "reasoning", None
        )

        if not reasoning:
            content, reasoning = self._split_inline_think_block(content)

        if self.thinking_enabled and not reasoning:
            logger.warning(
                "VLLM_ENABLE_THINKING is true but the model/endpoint "
                "(%s) did not return a separate reasoning field; "
                "continuing with content only.",
                self.model,
            )

        return LLMChatResult(content=content.strip(), reasoning=reasoning)

    @staticmethod
    def _split_inline_think_block(text: str) -> tuple[str, str | None]:
        """Fallback for servers that inline <think>...</think> into
        message.content instead of a dedicated reasoning field. Splits it
        into (content, reasoning) structurally rather than discarding it."""
        match = _THINK_BLOCK_RE.search(text)
        if not match:
            return text, None
        reasoning = match.group(1).strip() or None
        content = _THINK_BLOCK_RE.sub("", text).strip()
        return content, reasoning

    def generate_sql(self, user_question: str, schema_prompt: str) -> str:
        temperature = float(os.getenv("QWEN_TEMPERATURE_SQL", "0.1"))
        max_tokens = int(os.getenv("QWEN_MAX_TOKENS_SQL", "1024"))

        messages = [
            {"role": "system", "content": schema_prompt},
            {"role": "user", "content": user_question},
        ]
        result = self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        return self._clean_sql(result.content)

    def narrate_answer(
        self,
        user_question: str,
        sql: str,
        rows_preview: str,
        business_context: str = "",
    ) -> str:
        temperature = float(os.getenv("QWEN_TEMPERATURE_ANSWER", "0.2"))
        max_tokens = int(os.getenv("QWEN_MAX_TOKENS_ANSWER", "1200"))

        from app.core.domain_config import get_domain_config
        dc = get_domain_config()
        _fallback_narrate = (
            f"Anda adalah assistant analitik {dc.business_name}.\n"
            "Jawab dalam Bahasa Indonesia.\n"
            "Gunakan gaya ringkas, bisnis, dan mudah dipahami.\n"
            "Jangan menyebut data PII.\n"
            "Jangan mengarang angka di luar hasil query.\n"
            "Jika hasil kosong, jelaskan bahwa data tidak ditemukan untuk filter tersebut."
        )
        system_prompt = dc.prompt_answer_agent or _fallback_narrate

        user_prompt = f"""
Pertanyaan user:
{user_question}

SQL yang dijalankan:
{sql}

Preview hasil query:
{rows_preview}

Konteks bisnis tambahan:
{business_context}

Buat jawaban akhir dalam Bahasa Indonesia.
""".strip()

        result = self.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result.content

    @staticmethod
    def _clean_sql(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```sql", "").replace("```", "").strip()
        # Remove trailing explanation if model produced extra text after semicolon.
        if ";" in cleaned:
            cleaned = cleaned.split(";")[0].strip() + ";"
        return cleaned
