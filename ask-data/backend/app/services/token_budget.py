"""
Guards against sending prompts that exceed the vLLM server's
--max-model-len (VLLM_MAX_MODEL_LEN on the vLLM Application). Without
this, an oversized prompt fails as a raw BadRequestError surfaced to
the user (see: "This model's maximum context length is 4096 tokens...").

This never changes what the model can accept — it only trims the parts
of OUR prompt that are safe to shrink (conversation history, then the
SQL result-row preview) before the request is sent, so a user gets a
slightly less context-rich but still correct answer instead of a raw
500/400 error.

Token counts here are estimates (chars / 4), not an exact tokenizer —
good enough for a safety margin, not for billing or precision limits.
"""

from __future__ import annotations

CHARS_PER_TOKEN_ESTIMATE = 4

# Keep a buffer below the hard limit: our estimate is approximate, and
# other providers (Azure/Bedrock) have their own headroom too.
SAFETY_MARGIN_RATIO = 0.85


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN_ESTIMATE)


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    return sum(estimate_tokens(m.get("content", "")) for m in messages)


def available_input_budget(max_model_len: int, max_output_tokens: int) -> int:
    """How many input tokens we can safely spend, leaving room for the
    requested output and a safety margin below the server's hard limit."""
    usable = int(max_model_len * SAFETY_MARGIN_RATIO)
    return max(0, usable - max_output_tokens)


def fits_budget(
    messages: list[dict[str, str]],
    max_model_len: int,
    max_output_tokens: int,
) -> bool:
    return estimate_messages_tokens(messages) <= available_input_budget(
        max_model_len, max_output_tokens
    )
