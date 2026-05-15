"""
Optional FastAPI proxy wrapper for Qwen/vLLM.

Use this only if you want a thin application-owned endpoint in front of vLLM.
For simplest PoC, backend can call vLLM directly at QWEN_BASE_URL.

Run:
  uvicorn qwen_proxy_app:app --host 0.0.0.0 --port 8080
"""

import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field


QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "http://localhost:8000/v1")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "local-dev-token")
QWEN_MODEL = os.getenv("QWEN_MODEL", "Qwen/Qwen3-8B-AWQ")

client = OpenAI(base_url=QWEN_BASE_URL, api_key=QWEN_API_KEY)
app = FastAPI(title="Bank Jatim Qwen Proxy", version="0.1.0")


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=4096)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "provider": "local_qwen",
        "qwen_base_url": QWEN_BASE_URL,
        "qwen_model": QWEN_MODEL,
    }


@app.post("/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    try:
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=req.messages,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        return {
            "model": QWEN_MODEL,
            "content": response.choices[0].message.content,
            "usage": response.usage.model_dump() if response.usage else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Qwen inference failed: {exc}") from exc
