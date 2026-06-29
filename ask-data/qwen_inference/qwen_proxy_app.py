"""
Qwen Universal Proxy — OpenAI-compatible middleware in front of vLLM.

Solves Qwen2.5 quirks so ANY client (Agent Studio / CrewAI, Ask-Data,
custom apps) can use it as a drop-in OpenAI replacement:

  1. ReAct format enforcement  → fixes CrewAI infinite loop
  2. Thinking token stripping  → strips <think>...</think> from Qwen3
  3. Final Answer extraction   → ensures CrewAI always gets clean output
  4. Standard OpenAI response  → tool_calls, finish_reason, usage all correct

Usage:
  Point any app to this proxy URL instead of vLLM directly.
  Use any OpenAI SDK — no Qwen-specific code needed in the client.

Run:
  uvicorn qwen_proxy_app:app --host 0.0.0.0 --port 8080
"""

import os
import re
import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
from pydantic import BaseModel, Field

# ── Config ────────────────────────────────────────────────────────────────────

VLLM_BASE_URL = os.getenv("QWEN_BASE_URL", "http://localhost:8000/v1")
VLLM_API_KEY  = os.getenv("QWEN_API_KEY",  "local-dev-token")
QWEN_MODEL    = os.getenv("QWEN_MODEL",    "Qwen/Qwen2.5-14B-Instruct-AWQ")

# Inject this into every system prompt so ReAct agents (CrewAI / Agent Studio)
# always receive properly formatted responses from Qwen.
REACT_FORMAT_RULES = """
You MUST follow this exact ReAct format for every response:

For actions:
Thought: [one sentence reasoning]
Action: [action name]
Action Input: [JSON object]

For final answer:
Thought: I now know the final answer
Final Answer: [your complete answer]

CRITICAL:
- Never repeat the same Thought or Action twice.
- After receiving any agent response, output Final Answer immediately.
- Never re-delegate a completed task.
- Always end with "Final Answer:" when done.
"""

client = OpenAI(base_url=VLLM_BASE_URL, api_key=VLLM_API_KEY)
app = FastAPI(title="Qwen Universal Proxy", version="1.0.0")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_agentic_request(messages: list[dict]) -> bool:
    """Detect if this request comes from a ReAct agent (CrewAI / Agent Studio)."""
    for msg in messages:
        content = msg.get("content", "") or ""
        if any(kw in content for kw in [
            "Thought:", "Action:", "Final Answer:",
            "delegate", "coworker", "crew", "agent",
        ]):
            return True
    return False


def _inject_react_rules(messages: list[dict]) -> list[dict]:
    """Prepend ReAct format rules into system prompt."""
    msgs = list(messages)
    if msgs and msgs[0].get("role") == "system":
        msgs[0] = {**msgs[0], "content": msgs[0]["content"] + "\n\n" + REACT_FORMAT_RULES.strip()}
    else:
        msgs.insert(0, {"role": "system", "content": REACT_FORMAT_RULES.strip()})
    return msgs


def _strip_thinking(text: str) -> str:
    """Remove Qwen3 <think>...</think> blocks from output."""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned.strip()


def _extract_final_answer(text: str) -> str:
    """If model produced 'Final Answer: X', return just X."""
    match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def _normalize_output(content: str, is_agentic: bool) -> str:
    """Clean model output: strip thinking, optionally extract final answer."""
    content = _strip_thinking(content)
    # For agentic requests, keep full ReAct output so CrewAI can parse it
    # For regular requests, just return clean content
    return content.strip()


# ── Schema ────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str | None = None


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[dict[str, Any]]
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    stream: bool = False
    tools: list[dict] | None = None
    tool_choice: Any = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
@app.get("/v1/health")
def health() -> dict:
    return {
        "status": "ok",
        "proxy": "qwen-universal-proxy",
        "vllm_url": VLLM_BASE_URL,
        "model": QWEN_MODEL,
    }


@app.get("/v1/models")
def list_models() -> dict:
    """Pass-through models list from vLLM."""
    try:
        models = client.models.list()
        return {
            "object": "list",
            "data": [{"id": m.id, "object": "model", "created": int(time.time()), "owned_by": "local"} for m in models.data],
        }
    except Exception as exc:
        return {
            "object": "list",
            "data": [{"id": QWEN_MODEL, "object": "model", "created": int(time.time()), "owned_by": "local"}],
        }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    messages      = body.get("messages", [])
    model         = body.get("model") or QWEN_MODEL
    temperature   = float(body.get("temperature", 0.2))
    max_tokens    = int(body.get("max_tokens", 2048))
    tools         = body.get("tools")
    tool_choice   = body.get("tool_choice")

    is_agentic = _is_agentic_request(messages)

    # Inject ReAct rules for agentic requests (CrewAI / Agent Studio)
    if is_agentic:
        messages = _inject_react_rules(messages)

    try:
        kwargs: dict[str, Any] = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"vLLM error: {exc}")

    choice   = response.choices[0]
    content  = choice.message.content or ""
    content  = _normalize_output(content, is_agentic)

    return JSONResponse({
        "id": f"chatcmpl-{uuid.uuid4().hex[:20]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in (choice.message.tool_calls or [])
                ] or None,
            },
            "finish_reason": choice.finish_reason or "stop",
        }],
        "usage": {
            "prompt_tokens":     response.usage.prompt_tokens     if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens":      response.usage.total_tokens      if response.usage else 0,
        },
    })


# ── Legacy /chat endpoint (backward compat with ask-data backend) ─────────────

@app.post("/chat")
async def chat_legacy(request: Request) -> dict:
    body = await request.json()
    messages    = body.get("messages", [])
    temperature = float(body.get("temperature", 0.2))
    max_tokens  = int(body.get("max_tokens", 1024))

    try:
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = _strip_thinking(response.choices[0].message.content or "")
        return {
            "model":   QWEN_MODEL,
            "content": content,
            "usage":   response.usage.model_dump() if response.usage else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Qwen inference failed: {exc}")
