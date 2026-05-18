"""
Local Qwen client for existing Ask Data backend.

Integration target:
- Replace Azure OpenAI / Bedrock calls with this client.
- vLLM exposes OpenAI-compatible /v1/chat/completions.
"""

import os
from typing import Any, Dict, List, Optional

from openai import OpenAI


class QwenClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("QWEN_BASE_URL", "http://localhost:8000/v1")
        self.api_key = os.getenv("QWEN_API_KEY", "bjt-local-vllm")
        self.model = os.getenv("QWEN_MODEL", "Qwen/Qwen3-8B-AWQ")
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
        extra_body: Optional[Dict[str, Any]] = None,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body or {},
        )
        return response.choices[0].message.content or ""

    def generate_sql(self, user_question: str, schema_prompt: str) -> str:
        temperature = float(os.getenv("QWEN_TEMPERATURE_SQL", "0.1"))
        max_tokens = int(os.getenv("QWEN_MAX_TOKENS_SQL", "1024"))

        messages = [
            {"role": "system", "content": schema_prompt},
            {"role": "user", "content": user_question},
        ]
        raw = self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        return self._clean_sql(raw)

    def narrate_answer(
        self,
        user_question: str,
        sql: str,
        rows_preview: str,
        business_context: str = "",
    ) -> str:
        temperature = float(os.getenv("QWEN_TEMPERATURE_ANSWER", "0.2"))
        max_tokens = int(os.getenv("QWEN_MAX_TOKENS_ANSWER", "1200"))

        system_prompt = """
Anda adalah assistant analitik Bank Jawa Timur.
Jawab dalam Bahasa Indonesia.
Gunakan gaya ringkas, bisnis, dan mudah dipahami.
Jangan menyebut data PII.
Jangan mengarang angka di luar hasil query.
Jika hasil kosong, jelaskan bahwa data tidak ditemukan untuk filter tersebut.
""".strip()

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

        return self.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @staticmethod
    def _clean_sql(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```sql", "").replace("```", "").strip()
        # Remove trailing explanation if model produced extra text after semicolon.
        if ";" in cleaned:
            cleaned = cleaned.split(";")[0].strip() + ";"
        return cleaned
