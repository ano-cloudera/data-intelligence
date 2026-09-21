# import os
# import time
# import requests

# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse, Response


# # =========================================================
# # Configuration
# # =========================================================

# VLLM_PORT = os.getenv(
#     "VLLM_INTERNAL_PORT",
#     "9000"
# )

# VLLM_BASE_URL = (
#     f"http://127.0.0.1:{VLLM_PORT}"
# )


# # =========================================================
# # Application
# # =========================================================

# app = FastAPI(
#     title="Tempo Scan LLM API",
#     description=(
#         "Cloudera AI proxy for vLLM "
#         "OpenAI-compatible API"
#     ),
#     version="1.0.0"
# )


# # =========================================================
# # Root
# # =========================================================

# @app.get("/")
# def root():

#     return {
#         "service": "Tempo Scan LLM",
#         "status": "running",
#         "backend": "vLLM",
#         "backend_url": VLLM_BASE_URL
#     }


# # =========================================================
# # Health
# # =========================================================

# @app.get("/health")
# def health():

#     try:

#         start = time.time()

#         response = requests.get(
#             f"{VLLM_BASE_URL}/health",
#             timeout=5
#         )

#         latency = round(
#             time.time() - start,
#             3
#         )


#         if response.status_code == 200:

#             return {
#                 "status": "ok",
#                 "backend": "vLLM",
#                 "vllm_status": 200,
#                 "latency_seconds": latency
#             }


#         return JSONResponse(
#             status_code=503,
#             content={
#                 "status": "degraded",
#                 "backend": "vLLM",
#                 "vllm_status": response.status_code,
#                 "response": response.text[:500]
#             }
#         )


#     except Exception as e:

#         return JSONResponse(
#             status_code=503,
#             content={
#                 "status": "error",
#                 "backend": "vLLM",
#                 "detail": str(e)
#             }
#         )


# # =========================================================
# # Models
# # =========================================================

# @app.get("/v1/models")
# def get_models():

#     try:

#         response = requests.get(
#             f"{VLLM_BASE_URL}/v1/models",
#             timeout=30
#         )


#         return Response(
#             content=response.content,
#             status_code=response.status_code,
#             media_type=(
#                 response.headers.get(
#                     "content-type",
#                     "application/json"
#                 )
#             )
#         )


#     except Exception as e:

#         return JSONResponse(
#             status_code=503,
#             content={
#                 "error": {
#                     "message": (
#                         "vLLM backend unavailable"
#                     ),
#                     "type": "backend_unavailable",
#                     "detail": str(e)
#                 }
#             }
#         )


# # =========================================================
# # Chat Completions
# # =========================================================

# @app.post("/v1/chat/completions")
# async def chat_completions(
#     request: Request
# ):

#     try:

#         body = await request.json()


#         print(
#             "Chat completion request:",
#             body.get("model")
#         )


#         response = requests.post(
#             (
#                 f"{VLLM_BASE_URL}"
#                 "/v1/chat/completions"
#             ),
#             json=body,
#             headers={
#                 "Content-Type":
#                 "application/json",

#                 "Accept":
#                 "application/json"
#             },
#             timeout=300
#         )


#         print(
#             "vLLM response status:",
#             response.status_code
#         )


#         if response.status_code != 200:

#             print(
#                 "vLLM response:",
#                 response.text[:2000]
#             )


#         return Response(
#             content=response.content,
#             status_code=response.status_code,
#             media_type=(
#                 response.headers.get(
#                     "content-type",
#                     "application/json"
#                 )
#             )
#         )


#     except Exception as e:

#         print(
#             "Chat proxy error:",
#             str(e)
#         )


#         return JSONResponse(
#             status_code=500,
#             content={
#                 "error": {
#                     "message": str(e),
#                     "type": "proxy_error"
#                 }
#             }
#         )


# # =========================================================
# # Optional Completion Endpoint
# # =========================================================

# @app.post("/v1/completions")
# async def completions(
#     request: Request
# ):

#     try:

#         body = await request.json()


#         response = requests.post(
#             (
#                 f"{VLLM_BASE_URL}"
#                 "/v1/completions"
#             ),
#             json=body,
#             headers={
#                 "Content-Type":
#                 "application/json"
#             },
#             timeout=300
#         )


#         return Response(
#             content=response.content,
#             status_code=response.status_code,
#             media_type=(
#                 response.headers.get(
#                     "content-type",
#                     "application/json"
#                 )
#             )
#         )


#     except Exception as e:

#         return JSONResponse(
#             status_code=500,
#             content={
#                 "error": {
#                     "message": str(e),
#                     "type": "proxy_error"
#                 }
#             }
#         )
import os
import json
import httpx

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse


# =========================================================
# CONFIGURATION
# =========================================================

VLLM_PORT = os.getenv(
    "VLLM_INTERNAL_PORT",
    "9000"
)

VLLM_BASE_URL = os.getenv(
    "VLLM_BASE_URL",
    f"http://127.0.0.1:{VLLM_PORT}"
)

ENABLE_THINKING = (
    os.getenv(
        "VLLM_ENABLE_THINKING",
        "false"
    ).lower()
    == "true"
)

# Caps how many reasoning tokens vLLM spends per request before it is
# forced to close the <think> block and start answering. Unset/blank/0
# means "no explicit cap" (only the normal max_tokens limit applies).
# There is no vLLM CLI flag for this — it only exists as a per-request
# root-level field, so the proxy is the single place that applies it as
# a server-wide default (same single-source-of-truth pattern as
# VLLM_ENABLE_THINKING above).
_raw_thinking_budget = os.getenv(
    "VLLM_THINKING_BUDGET",
    ""
).strip()

THINKING_TOKEN_BUDGET = (
    int(_raw_thinking_budget)
    if _raw_thinking_budget.isdigit()
    and int(_raw_thinking_budget) > 0
    else None
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Tempo Scan LLM API",
    version="1.0.0",
    description=(
        "Cloudera AI proxy for vLLM "
        "OpenAI-compatible API"
    )
)


# =========================================================
# HELPERS
# =========================================================

def normalize_messages(messages):
    """
    Normalize messages for Qwen/vLLM compatibility.

    Rules:
    1. Merge all system messages.
    2. Treat developer messages as system instructions.
    3. Put exactly one system message at the beginning.
    4. Preserve order of all non-system messages.
    """

    if not messages:
        return messages

    system_parts = []
    non_system_messages = []

    for message in messages:

        role = message.get(
            "role"
        )

        content = message.get(
            "content",
            ""
        )

        if role in (
            "system",
            "developer"
        ):

            if content:
                system_parts.append(
                    content
                )

        else:

            non_system_messages.append(
                message
            )

    normalized = []

    if system_parts:

        normalized.append(
            {
                "role": "system",
                "content": "\n\n".join(
                    system_parts
                )
            }
        )

    normalized.extend(
        non_system_messages
    )

    return normalized


def print_message_roles(
    label,
    messages
):
    try:

        roles = [
            message.get("role")
            for message
            in messages
        ]

        print(
            f"{label}: {roles}",
            flush=True
        )

    except Exception:

        pass


def safe_json_error(
    message,
    error_type="proxy_error",
    status_code=500
):

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "message": str(
                    message
                ),
                "type": error_type
            }
        }
    )


# =========================================================
# ROOT
# =========================================================

@app.get("/")
async def root():

    return {
        "service": "Tempo Scan LLM",
        "status": "running",
        "backend": "vLLM",
        "backend_url": VLLM_BASE_URL,
        "thinking_enabled": ENABLE_THINKING,
        "thinking_token_budget": THINKING_TOKEN_BUDGET
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def health():

    try:

        async with httpx.AsyncClient(
            timeout=10
        ) as client:

            response = await client.get(
                f"{VLLM_BASE_URL}/v1/models"
            )

        if response.status_code == 200:

            return {
                "status": "ok",
                "backend": "vLLM",
                "thinking_enabled": ENABLE_THINKING,
                "thinking_token_budget": THINKING_TOKEN_BUDGET
            }

        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "backend_status": (
                    response.status_code
                )
            }
        )

    except Exception as exc:

        return safe_json_error(
            exc,
            error_type="health_error",
            status_code=503
        )


# =========================================================
# MODELS
# =========================================================

@app.get("/v1/models")
async def get_models():

    try:

        async with httpx.AsyncClient(
            timeout=30
        ) as client:

            response = await client.get(
                f"{VLLM_BASE_URL}/v1/models"
            )

        content_type = (
            response.headers.get(
                "content-type",
                ""
            )
        )

        if (
            "application/json"
            in content_type
        ):

            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )

        return JSONResponse(
            status_code=response.status_code,
            content={
                "raw_response": (
                    response.text
                )
            }
        )

    except Exception as exc:

        return safe_json_error(
            exc
        )


# =========================================================
# CHAT COMPLETIONS
# =========================================================

@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request
):

    try:

        payload = await request.json()

    except Exception as exc:

        return safe_json_error(
            f"Invalid JSON body: {exc}",
            error_type="invalid_request",
            status_code=400
        )


    # =====================================================
    # DEBUG RAW ROLES
    # =====================================================

    raw_messages = payload.get(
        "messages",
        []
    )

    print_message_roles(
        "RAW MESSAGE ROLES",
        raw_messages
    )


    # =====================================================
    # NORMALIZE AGENT STUDIO / LITELLM MESSAGES
    # =====================================================

    if raw_messages:

        payload[
            "messages"
        ] = normalize_messages(
            raw_messages
        )


    normalized_messages = payload.get(
        "messages",
        []
    )

    print_message_roles(
        "NORMALIZED MESSAGE ROLES",
        normalized_messages
    )


    # =====================================================
    # THINKING CONFIGURATION
    # =====================================================

    chat_template_kwargs = (
        payload.get(
            "chat_template_kwargs",
            {}
        )
        or {}
    )

    chat_template_kwargs[
        "enable_thinking"
    ] = ENABLE_THINKING

    payload[
        "chat_template_kwargs"
    ] = chat_template_kwargs


    # thinking_token_budget is a root-level field (not inside
    # chat_template_kwargs) understood directly by vLLM's sampler. Only
    # apply it when thinking is actually enabled and a positive budget is
    # configured — forcing it while thinking is off has no effect and
    # would just be a confusing no-op field on every request.
    if (
        ENABLE_THINKING
        and THINKING_TOKEN_BUDGET is not None
    ):

        payload[
            "thinking_token_budget"
        ] = THINKING_TOKEN_BUDGET


    print(
        "Thinking mode enabled:",
        ENABLE_THINKING,
        "| thinking_token_budget:",
        THINKING_TOKEN_BUDGET if ENABLE_THINKING else None,
        flush=True
    )


    # =====================================================
    # STREAMING REQUEST
    # =====================================================

    stream = bool(
        payload.get(
            "stream",
            False
        )
    )


    if stream:

        async def stream_generator():

            try:

                async with httpx.AsyncClient(
                    timeout=None
                ) as client:

                    async with client.stream(
                        "POST",
                        (
                            f"{VLLM_BASE_URL}"
                            "/v1/chat/completions"
                        ),
                        json=payload,
                        headers={
                            "Content-Type":
                                "application/json"
                        }
                    ) as response:

                        async for chunk in (
                            response.aiter_raw()
                        ):

                            yield chunk

            except Exception as exc:

                error_payload = {
                    "error": {
                        "message": str(
                            exc
                        ),
                        "type":
                            "stream_proxy_error"
                    }
                }

                yield (
                    json.dumps(
                        error_payload
                    )
                    .encode(
                        "utf-8"
                    )
                )

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )


    # =====================================================
    # NON-STREAMING REQUEST
    # =====================================================

    try:

        async with httpx.AsyncClient(
            timeout=600
        ) as client:

            response = await client.post(
                (
                    f"{VLLM_BASE_URL}"
                    "/v1/chat/completions"
                ),
                json=payload,
                headers={
                    "Content-Type":
                        "application/json"
                }
            )


        content_type = (
            response.headers.get(
                "content-type",
                ""
            )
        )


        if (
            "application/json"
            in content_type
        ):

            return JSONResponse(
                status_code=(
                    response.status_code
                ),
                content=response.json()
            )


        return JSONResponse(
            status_code=(
                response.status_code
            ),
            content={
                "raw_response":
                    response.text
            }
        )


    except Exception as exc:

        return safe_json_error(
            exc
        )


# =========================================================
# COMPLETIONS
# =========================================================

@app.post("/v1/completions")
async def completions(
    request: Request
):

    try:

        payload = await request.json()

    except Exception as exc:

        return safe_json_error(
            f"Invalid JSON body: {exc}",
            error_type="invalid_request",
            status_code=400
        )


    stream = bool(
        payload.get(
            "stream",
            False
        )
    )


    # =====================================================
    # STREAMING
    # =====================================================

    if stream:

        async def stream_generator():

            try:

                async with httpx.AsyncClient(
                    timeout=None
                ) as client:

                    async with client.stream(
                        "POST",
                        (
                            f"{VLLM_BASE_URL}"
                            "/v1/completions"
                        ),
                        json=payload,
                        headers={
                            "Content-Type":
                                "application/json"
                        }
                    ) as response:

                        async for chunk in (
                            response.aiter_raw()
                        ):

                            yield chunk

            except Exception as exc:

                error_payload = {
                    "error": {
                        "message":
                            str(exc),
                        "type":
                            "stream_proxy_error"
                    }
                }

                yield (
                    json.dumps(
                        error_payload
                    )
                    .encode(
                        "utf-8"
                    )
                )


        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )


    # =====================================================
    # NON-STREAMING
    # =====================================================

    try:

        async with httpx.AsyncClient(
            timeout=600
        ) as client:

            response = await client.post(
                (
                    f"{VLLM_BASE_URL}"
                    "/v1/completions"
                ),
                json=payload,
                headers={
                    "Content-Type":
                        "application/json"
                }
            )


        content_type = (
            response.headers.get(
                "content-type",
                ""
            )
        )


        if (
            "application/json"
            in content_type
        ):

            return JSONResponse(
                status_code=(
                    response.status_code
                ),
                content=response.json()
            )


        return JSONResponse(
            status_code=(
                response.status_code
            ),
            content={
                "raw_response":
                    response.text
            }
        )


    except Exception as exc:

        return safe_json_error(
            exc
        )