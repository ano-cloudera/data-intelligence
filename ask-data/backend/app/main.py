import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.connection import (
    ImpalaConnectionError,
    ImpalaQueryError,
    check_impala_health,
    run_query,
    run_query_with_metadata,
)
from app.schemas.analytics import AnalyticsEventsResponse, AnalyticsSummaryResponse
from app.schemas.llm import (
    LLMProviderOptionsResponse,
    LLMProviderSelectionRequest,
    LLMProviderSelectionResponse,
)
from app.schemas.rag import (
    RagOptionsResponse,
    RagSessionConfigRequest,
    RagSessionConfigResponse,
)
from app.schemas.session import SessionDetailResponse, SessionListResponse
from pydantic import BaseModel as _BaseModel


class TableLockRequest(_BaseModel):
    session_id: str
    locked_table: str | None = None


class TableLockResponse(_BaseModel):
    session_id: str
    locked_table: str | None = None
from app.schemas.sql import (
    ChatAnswerResponse,
    ChatQueryRequest,
    ChatQueryResponse,
    SQLExecuteRequest,
    SQLExecutionResponse,
    SQLGenerateRequest,
    SQLGenerationResponse,
)
from app.services.memory_store import SessionMemoryStore
from app.services.analytics_store import (
    InMemoryAnalyticsStore,
    SQLiteAnalyticsStore,
    estimate_text_tokens,
)
from app.services.answer_generator import AnswerGeneratorService
from app.services.chat_router import (
    build_processing_fallback_answer,
    extract_visualization_preference,
    is_greeting_or_smalltalk,
    is_visualization_followup,
    looks_like_data_request,
    is_acknowledgement,
    is_farewell,
)
from app.services.rag_client import ChromaRagClient, RagClientError
from app.services.conversation_generator import ConversationGeneratorService
from app.services.llm_provider_service import LLMProviderService
from app.services.llm_router import LLMRouter
from app.services.session_store import InMemorySessionStore, SQLiteSessionStore
from app.services.sql_executor import SQLExecutionError, SQLExecutorService
from app.services.sql_generator import SQLGeneratorService
from app.services.sql_guardrails import SQLValidationError
from app.services.guardrails_service import GuardrailsDecision, GuardrailsService, GuardrailsServiceError
from app.services.visualization_service import VisualizationService

settings = get_settings()
logger = logging.getLogger(__name__)


def _build_session_store():
    if settings.session_backend.strip().lower() == "sqlite":
        return SQLiteSessionStore(settings)
    return InMemorySessionStore(settings)


def _build_analytics_store():
    if settings.session_backend.strip().lower() == "sqlite":
        return SQLiteAnalyticsStore(settings)
    return InMemoryAnalyticsStore(settings)


session_store = _build_session_store()
analytics_store = _build_analytics_store()
memory_store = SessionMemoryStore(session_store=session_store, settings=settings)
llm_provider_service = LLMProviderService(settings=settings)
llm_router = LLMRouter(settings=settings, provider_service=llm_provider_service)
sql_generator = SQLGeneratorService(
    llm_router=llm_router,
    memory_store=memory_store,
    settings=settings,
)
sql_executor = SQLExecutorService(settings=settings)
answer_generator = AnswerGeneratorService(llm_router=llm_router, settings=settings)
conversation_generator = ConversationGeneratorService(llm_router=llm_router, settings=settings)
rag_client = ChromaRagClient(settings=settings) if settings.is_rag_configured else None
guardrails_service = GuardrailsService(settings=settings)
visualization_service = VisualizationService()

logger.info("ask-data backend startup complete")

app = FastAPI(
    title="Ask Data Backend",
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> dict[str, object]:
    return {
        "message": "Ask Data backend is running.",
        "app": "ask-data",
        "environment": settings.app_env,
        "database": settings.impala_db,
        "guardrails": guardrails_service.get_runtime_status(),
        "session_backend": settings.session_backend,
        "llm_providers": [option.provider for option in llm_provider_service.list_options().options],
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "ask-data-backend",
        "environment": settings.app_env,
        "debug": settings.app_debug,
        "guardrails": guardrails_service.get_runtime_status(),
        "session_backend": settings.session_backend,
        "llm_provider": settings.llm_provider,
        "qwen_base_url": settings.qwen_base_url,
        "qwen_model": settings.qwen_model,
        "llm_providers": [option.provider for option in llm_provider_service.list_options().options],
    }


@app.get("/health/db")
def health_db() -> dict[str, object]:
    try:
        return check_impala_health()
    except ImpalaConnectionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ImpalaQueryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/tables")
def list_tables() -> dict[str, object]:
    try:
        rows = run_query(f"SHOW TABLES IN {settings.impala_db}")
    except ImpalaConnectionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ImpalaQueryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    tables = []
    for row in rows:
        if row:
            tables.append(next(iter(row.values())))

    return {
        "status": "ok",
        "database": settings.impala_db,
        "count": len(tables),
        "tables": tables,
    }


@app.get("/tables/{table_name}/preview")
def get_table_preview(table_name: str) -> dict[str, object]:
    table_clean = table_name.strip().lower()
    allowed = settings.sql_allowed_tables_list
    db = settings.impala_db.lower()
    qualified = f"{db}.{table_clean}"
    if table_clean not in allowed and qualified not in allowed:
        raise HTTPException(status_code=403, detail=f"Table not allowed: {table_name}")
    try:
        result = run_query_with_metadata(
            f"SELECT * FROM {settings.impala_db}.{table_clean} LIMIT 10"
        )
        return {
            "status": "ok",
            "table": table_clean,
            "columns": result["columns"],
            "rows": result["rows"],
        }
    except ImpalaConnectionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ImpalaQueryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/sessions", response_model=SessionListResponse)
def list_sessions(limit: int = 20) -> SessionListResponse:
    safe_limit = max(1, min(limit, 50))
    return SessionListResponse(sessions=memory_store.list_sessions(limit=safe_limit))


@app.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: str) -> SessionDetailResponse:
    session = memory_store.get_session_state(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return SessionDetailResponse(session=session)


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str) -> dict[str, str]:
    deleted = memory_store.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"status": "deleted", "session_id": session_id}


@app.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
def analytics_summary(window_days: int = 30) -> AnalyticsSummaryResponse:
    safe_window = max(1, min(window_days, 365))
    return analytics_store.get_summary(window_days=safe_window)


@app.get("/analytics/events", response_model=AnalyticsEventsResponse)
def analytics_events(limit: int = 20) -> AnalyticsEventsResponse:
    safe_limit = max(1, min(limit, 100))
    return analytics_store.list_events(limit=safe_limit)


@app.get("/llm/providers", response_model=LLMProviderOptionsResponse)
def get_llm_provider_options(session_id: str | None = None) -> LLMProviderOptionsResponse:
    session_memory = memory_store.get_session_state(session_id) if session_id else None
    return llm_provider_service.list_options(
        session_id=session_id,
        session_memory=session_memory,
    )


@app.post("/llm/providers/select", response_model=LLMProviderSelectionResponse)
def select_llm_provider(payload: LLMProviderSelectionRequest) -> LLMProviderSelectionResponse:
    req_provider = payload.provider.strip().lower()
    if req_provider == "bedrock" and payload.model_id:
        mid = payload.model_id.strip()
        if mid not in llm_provider_service.bedrock_catalog_ids():
            raise HTTPException(
                status_code=422,
                detail="Unknown Bedrock model_id for this deployment.",
            )
    session = memory_store.get_or_create_session(payload.session_id)
    session = llm_provider_service.apply_selection(
        session,
        payload.provider,
        payload.model_id,
    )
    persisted = memory_store.set_llm_selection(payload.session_id, session.llm_selection)
    _log_analytics_event(
        event_type="provider-select",
        endpoint="/llm/providers/select",
        session_id=payload.session_id,
        mode="provider-select",
        provider=persisted.llm_selection.provider,
        model_name=persisted.llm_selection.model_name,
        success=True,
        question_excerpt=f"Provider set to {persisted.llm_selection.provider}",
    )
    return LLMProviderSelectionResponse(
        session_id=payload.session_id,
        active_provider=persisted.llm_selection.provider,
        active_model_id=persisted.llm_selection.model_id,
        active_model_name=persisted.llm_selection.model_name,
    )


def _store_result_preview(session_id: str | None, execution_result: dict[str, object]) -> None:
    if not session_id:
        return

    memory_store.set_last_result_preview(
        session_id=session_id,
        columns=execution_result["columns"],
        rows=execution_result["rows"],
        row_count=execution_result["row_count"],
        truncated=execution_result["truncated"],
    )


def _safe_question_excerpt(question: str, max_length: int = 120) -> str:
    cleaned = " ".join(question.split())
    if len(cleaned) <= max_length:
        return cleaned
    return f"{cleaned[: max_length - 1].rstrip()}…"


def _log_analytics_event(
    *,
    event_type: str,
    endpoint: str,
    session_id: str | None = None,
    mode: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    success: bool = True,
    guardrails_action: str | None = None,
    visualization_type: str | None = None,
    estimated_prompt_tokens: int = 0,
    estimated_completion_tokens: int = 0,
    question_excerpt: str | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    try:
        analytics_store.log_event(
            event_type=event_type,
            endpoint=endpoint,
            session_id=session_id,
            mode=mode,
            provider=provider,
            model_name=model_name,
            success=success,
            guardrails_action=guardrails_action,
            visualization_type=visualization_type,
            estimated_prompt_tokens=estimated_prompt_tokens,
            estimated_completion_tokens=estimated_completion_tokens,
            question_excerpt=question_excerpt,
            metadata=metadata,
        )
    except Exception as exc:  # pragma: no cover - observability must never break chat flow
        logger.warning("analytics logging failed: %s", exc)


def _infer_chat_mode(response_payload: dict[str, object]) -> str:
    metadata = response_payload.get("metadata")
    if isinstance(metadata, dict):
        if metadata.get("guardrails_action") == "block":
            return "guardrails-block"
        if metadata.get("visualization_followup") is True:
            return "visualization-followup"
    if response_payload.get("mode") == "rag":
        return "rag"
    if response_payload.get("mode") == "fallback":
        return "fallback"
    if response_payload.get("generated_sql"):
        return "chat-query"
    if response_payload.get("rows"):
        return "chat-query"
    return "conversation"


def _log_chat_response(
    *,
    endpoint: str,
    payload: ChatQueryRequest,
    response_payload: dict[str, object],
) -> None:
    metadata = response_payload.get("metadata")
    metadata_dict = metadata if isinstance(metadata, dict) else {}
    question_excerpt = _safe_question_excerpt(payload.question)
    answer = str(response_payload.get("answer") or "")
    generated_sql = str(response_payload.get("generated_sql") or response_payload.get("executed_sql") or "")
    mode = _infer_chat_mode(response_payload)
    provider = metadata_dict.get("provider")
    model_name = metadata_dict.get("model")
    visualization = response_payload.get("visualization")
    visualization_type = None
    if isinstance(visualization, dict):
        visualization_type = visualization.get("type") if isinstance(visualization.get("type"), str) else None

    prompt_tokens = estimate_text_tokens(payload.question, generated_sql)
    completion_tokens = estimate_text_tokens(answer)

    _log_analytics_event(
        event_type=endpoint.strip("/").replace("/", "-"),
        endpoint=endpoint,
        session_id=payload.session_id,
        mode=mode,
        provider=provider if isinstance(provider, str) else None,
        model_name=model_name if isinstance(model_name, str) else None,
        success=True,
        guardrails_action=metadata_dict.get("guardrails_action") if isinstance(metadata_dict.get("guardrails_action"), str) else None,
        visualization_type=visualization_type,
        estimated_prompt_tokens=prompt_tokens,
        estimated_completion_tokens=completion_tokens,
        question_excerpt=question_excerpt,
        metadata={
            "row_count": response_payload.get("row_count", 0),
            "truncated": response_payload.get("truncated", False),
            "limit_applied": response_payload.get("limit_applied", False),
        },
    )


def _maybe_block_with_guardrails(question: str) -> GuardrailsDecision | None:
    if not settings.guardrails_enabled:
        return None

    decision = guardrails_service.screen_question(question)
    if decision.action == "block":
        return decision
    return None


def _guardrails_block_response(
    payload: ChatQueryRequest,
    decision: GuardrailsDecision,
) -> dict[str, object]:
    answer = decision.message or build_processing_fallback_answer(payload.question)
    if payload.session_id:
        memory_store.append_user_message(payload.session_id, payload.question)
        memory_store.append_assistant_message(payload.session_id, answer)
        memory_store.set_last_answer(payload.session_id, answer)
        memory_store.set_last_intent(payload.session_id, "guardrails-block")

    return {
        "session_id": payload.session_id,
        "original_question": payload.question,
        "answer": answer,
        "generated_sql": "",
        "executed_sql": "",
        "columns": [],
        "rows": [],
        "row_count": 0,
        "truncated": False,
        "limit_applied": False,
        "metadata": {
            "guardrails_action": decision.action,
            "guardrails_reason": decision.reason,
            **decision.metadata,
        },
        "visualization": None,
    }


def _apply_output_guardrails(
    payload: ChatQueryRequest,
    answer: str,
) -> tuple[str, dict[str, object]]:
    if not settings.guardrails_enabled:
        return answer, {}

    decision = guardrails_service.protect_answer_text(payload.question, answer)
    if decision.action == "block":
        return (
            decision.message or build_processing_fallback_answer(payload.question),
            {
                "guardrails_action": decision.action,
                "guardrails_reason": decision.reason,
                **decision.metadata,
            },
        )
    if decision.action == "redact":
        return (
            decision.message or answer,
            {
                "guardrails_action": decision.action,
                "guardrails_reason": decision.reason,
                **decision.metadata,
            },
        )
    return decision.message or answer, {}


def _build_visualization_followup_answer(question: str, preferred_type: str) -> str:
    preferred_label = {
        "bar": "bar chart",
        "line": "line chart",
        "pie": "pie chart",
        "table": "table",
    }.get(preferred_type, "chart")

    if " " not in preferred_label and preferred_label.endswith("chart"):
        preferred_label = preferred_label.replace("chart", " chart")

    if "table" == preferred_type:
        if " " in question.lower() or any(token in question.lower() for token in ("tabel", "table")):
            return "Saya menampilkan ulang hasil terakhir dalam bentuk tabel agar lebih mudah dibandingkan."
        return "The latest result has been reformatted as a table for easier review."

    if any(word in question.lower() for word in ("ubah", "ganti", "jadikan", "tampilkan", "bentuk", "grafik", "chart")):
        return f"Saya menampilkan ulang hasil terakhir dalam bentuk {preferred_label} tanpa mengubah data dasarnya."
    return f"The latest result has been re-rendered as a {preferred_label} without changing the underlying data."


def _maybe_handle_visualization_followup(
    payload: ChatQueryRequest,
    session_memory,
) -> dict[str, object] | None:
    if not payload.session_id or session_memory is None:
        return None
    if not is_visualization_followup(payload.question):
        return None
    if session_memory.last_result_preview is None or not session_memory.last_result_preview.rows:
        return None

    preferred_type = extract_visualization_preference(payload.question)
    if preferred_type is None:
        return None

    preview = session_memory.last_result_preview
    visualization = visualization_service.build_visualization(
        question=payload.question,
        columns=preview.columns,
        rows=preview.rows,
        preferred_type=preferred_type,
    )
    if visualization is None:
        return None

    answer = _build_visualization_followup_answer(payload.question, visualization.type or preferred_type)
    if payload.session_id:
        memory_store.append_user_message(payload.session_id, payload.question)
        memory_store.append_assistant_message(payload.session_id, answer)
        memory_store.set_last_answer(payload.session_id, answer)
        memory_store.set_last_intent(payload.session_id, "visualization-followup")

    return {
        "session_id": payload.session_id,
        "original_question": payload.question,
        "answer": answer,
        "generated_sql": session_memory.last_generated_sql or "",
        "executed_sql": session_memory.last_generated_sql or "",
        "columns": preview.columns,
        "rows": preview.rows,
        "row_count": preview.row_count,
        "truncated": preview.truncated,
        "limit_applied": False,
        "metadata": {
            "visualization_followup": True,
            "preferred_chart_type": preferred_type,
        },
        "visualization": visualization.model_dump(),
    }


def _run_chat_flow(payload: ChatQueryRequest) -> dict[str, object]:
    blocked_decision = _maybe_block_with_guardrails(payload.question)
    if blocked_decision is not None:
        return _guardrails_block_response(payload, blocked_decision)

    session_memory = None
    if payload.session_id:
        session_memory = memory_store.get_or_create_session(payload.session_id)

    visualization_followup_response = _maybe_handle_visualization_followup(payload, session_memory)
    if visualization_followup_response is not None:
        return visualization_followup_response

    if (
        is_greeting_or_smalltalk(payload.question)
        or is_farewell(payload.question)
        or is_acknowledgement(payload.question)
        or not looks_like_data_request(payload.question)
    ):
        answer = conversation_generator.generate_response(
            question=payload.question,
            memory=session_memory,
        )
        if payload.session_id:
            memory_store.append_user_message(payload.session_id, payload.question)
            memory_store.append_assistant_message(payload.session_id, answer)
            memory_store.set_last_answer(payload.session_id, answer)
            memory_store.set_last_intent(payload.session_id, "conversation")

        return {
            "session_id": payload.session_id,
            "original_question": payload.question,
            "answer": answer,
            "generated_sql": "",
            "executed_sql": "",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "limit_applied": False,
            "metadata": {},
            "visualization": None,
        }

    table_lock = memory_store.get_table_lock(payload.session_id) if payload.session_id else None
    session_locked_table = table_lock.locked_table if table_lock else None

    try:
        generated = sql_generator.generate_sql(
            question=payload.question,
            memory=session_memory,
        )
        execution_result = sql_executor.execute(
            generated["cleaned_generated_sql"],
            session_locked_table=session_locked_table,
        )
    except SQLValidationError:
        answer = conversation_generator.generate_response(
            question=payload.question,
            memory=session_memory,
        )
        if payload.session_id:
            memory_store.append_user_message(payload.session_id, payload.question)
            memory_store.append_assistant_message(payload.session_id, answer)
            memory_store.set_last_answer(payload.session_id, answer)
            memory_store.set_last_intent(payload.session_id, "conversation")

        return {
            "session_id": payload.session_id,
            "original_question": payload.question,
            "answer": answer,
            "generated_sql": "",
            "executed_sql": "",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "limit_applied": False,
            "metadata": {},
            "visualization": None,
        }

    result_decision = guardrails_service.screen_result_columns(
        question=payload.question,
        columns=execution_result["columns"],
    )
    if result_decision.action == "block":
        return _guardrails_block_response(payload, result_decision)

    visualization = visualization_service.build_visualization(
        question=payload.question,
        columns=execution_result["columns"],
        rows=execution_result["rows"],
    )
    answer = answer_generator.generate_answer(
        original_question=payload.question,
        executed_sql=execution_result["executed_sql"],
        columns=execution_result["columns"],
        rows=execution_result["rows"],
        row_count=execution_result["row_count"],
        truncated=execution_result["truncated"],
        limit_applied=execution_result["limit_applied"],
        memory=session_memory,
    )
    answer, output_guardrails_metadata = _apply_output_guardrails(payload, answer)
    _store_result_preview(payload.session_id, execution_result)
    if payload.session_id:
        memory_store.append_user_message(payload.session_id, payload.question)
        memory_store.append_assistant_message(payload.session_id, answer)
        memory_store.set_last_generated_sql(
            payload.session_id,
            generated["cleaned_generated_sql"],
        )
        memory_store.set_last_answer(payload.session_id, answer)
        memory_store.set_last_intent(payload.session_id, "chat-query")

    return {
        "session_id": payload.session_id,
        "original_question": payload.question,
        "answer": answer,
        "generated_sql": generated["cleaned_generated_sql"],
        "executed_sql": execution_result["executed_sql"],
        "columns": execution_result["columns"],
        "rows": execution_result["rows"],
        "row_count": execution_result["row_count"],
        "truncated": execution_result["truncated"],
        "limit_applied": execution_result["limit_applied"],
        "metadata": {
            "provider": generated["provider"],
            "model": generated["model"],
            "deployment": generated["deployment"],
            **output_guardrails_metadata,
        },
        "visualization": visualization.model_dump() if visualization is not None else None,
    }


def _get_rag_config_response(session_id: str) -> RagSessionConfigResponse:
    rag_config = memory_store.get_rag_config(session_id)
    if rag_config is None:
        return RagSessionConfigResponse(session_id=session_id)
    return RagSessionConfigResponse(
        session_id=session_id,
        enabled=rag_config.enabled,
        collection_name=rag_config.collection_name,
        top_k=rag_config.top_k,
    )


def _validate_rag_config(payload: RagSessionConfigRequest) -> None:
    if not payload.enabled:
        return
    if not payload.collection_name:
        raise HTTPException(
            status_code=400,
            detail="RAG configuration is incomplete. Please select a collection.",
        )


def _run_rag_chat_flow(payload: ChatQueryRequest) -> dict[str, object]:
    blocked_decision = _maybe_block_with_guardrails(payload.question)
    if blocked_decision is not None:
        blocked_payload = _guardrails_block_response(payload, blocked_decision)
        return {
            "session_id": blocked_payload["session_id"],
            "original_question": blocked_payload["original_question"],
            "answer": blocked_payload["answer"],
            "mode": "guardrails-block",
            "sources": [],
            "metadata": blocked_payload.get("metadata", {}),
            "visualization": None,
        }

    if rag_client is None:
        raise RagClientError("RAG (ChromaDB) is not configured for this backend.")
    if not payload.session_id:
        raise RagClientError("RAG requests require a session ID.")

    rag_config = memory_store.get_rag_config(payload.session_id)
    if rag_config is None or not rag_config.enabled or not rag_config.collection_name:
        raise RagClientError("RAG is not enabled or collection is not set for this session.")

    sources = rag_client.query(
        collection_name=rag_config.collection_name,
        question=payload.question,
        top_k=rag_config.top_k,
    )
    context_text = rag_client.build_context_text(sources)

    llm_client = llm_router.get_client()
    system_prompt = (
        "Anda adalah asisten analitik Bank Jawa Timur. "
        "Jawab berdasarkan konteks dokumen di bawah ini. "
        "Jika informasi tidak tersedia di dokumen, katakan 'Informasi tidak tersedia di dokumen yang ada.'"
    )
    user_prompt = (
        f"Konteks dokumen:\n{context_text}\n\n"
        f"Pertanyaan: {payload.question}"
    )
    answer = llm_client.chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    answer, output_guardrails_metadata = _apply_output_guardrails(payload, answer)

    memory_store.append_user_message(payload.session_id, payload.question)
    memory_store.append_assistant_message(payload.session_id, answer)
    memory_store.set_last_answer(payload.session_id, answer)
    memory_store.set_last_intent(payload.session_id, "rag")

    return {
        "session_id": payload.session_id,
        "original_question": payload.question,
        "answer": answer,
        "mode": "rag",
        "sources": sources,
        "metadata": output_guardrails_metadata,
        "visualization": None,
    }


@app.post("/sql/generate", response_model=SQLGenerationResponse)
def generate_sql(payload: SQLGenerateRequest) -> SQLGenerationResponse:
    try:
        generated = sql_generator.generate_sql(
            question=payload.question,
            session_id=payload.session_id,
        )
        return SQLGenerationResponse(**generated)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/sql/execute", response_model=SQLExecutionResponse)
def execute_sql(payload: SQLExecuteRequest) -> SQLExecutionResponse:
    try:
        execution_result = sql_executor.execute(payload.sql)
        _store_result_preview(payload.session_id, execution_result)
        return SQLExecutionResponse(**execution_result)
    except SQLValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLExecutionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/chat/query", response_model=ChatQueryResponse)
def chat_query(payload: ChatQueryRequest) -> ChatQueryResponse:
    try:
        response_payload = _run_chat_flow(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLExecutionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except GuardrailsServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    _log_chat_response(endpoint="/chat/query", payload=payload, response_payload=response_payload)
    return ChatQueryResponse(**response_payload)


@app.get("/rag/options", response_model=RagOptionsResponse)
def rag_options() -> RagOptionsResponse:
    if rag_client is None:
        return RagOptionsResponse(enabled=False, collections=[])
    try:
        cols = rag_client.list_collections()
        from app.schemas.rag import RagCollectionOption
        return RagOptionsResponse(
            enabled=True,
            collections=[RagCollectionOption(**c) for c in cols],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/rag/ingest")
def rag_ingest(collection_name: str, pdf_path: str) -> dict:
    if rag_client is None:
        raise HTTPException(status_code=400, detail="RAG (ChromaDB) is not configured.")
    try:
        count = rag_client.ingest_pdf(collection_name=collection_name, pdf_path=pdf_path)
        return {"collection": collection_name, "chunks_ingested": count}
    except RagClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/rag/config/{session_id}", response_model=RagSessionConfigResponse)
def get_rag_config(session_id: str) -> RagSessionConfigResponse:
    return _get_rag_config_response(session_id)


@app.post("/rag/config", response_model=RagSessionConfigResponse)
def save_rag_config(payload: RagSessionConfigRequest) -> RagSessionConfigResponse:
    if rag_client is None:
        raise HTTPException(status_code=400, detail="RAG (ChromaDB) is not configured for this backend.")
    _validate_rag_config(payload)
    try:
        memory_store.set_rag_config(payload)
        return _get_rag_config_response(payload.session_id)
    except HTTPException:
        raise
    except RagClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/table-lock/{session_id}", response_model=TableLockResponse)
def get_table_lock_endpoint(session_id: str) -> TableLockResponse:
    lock = memory_store.get_table_lock(session_id)
    return TableLockResponse(
        session_id=session_id,
        locked_table=lock.locked_table if lock else None,
    )


@app.post("/table-lock", response_model=TableLockResponse)
def set_table_lock_endpoint(payload: TableLockRequest) -> TableLockResponse:
    if payload.locked_table:
        allowed = set(settings.sql_allowed_tables_list)
        db = settings.impala_db.lower()
        candidate = payload.locked_table.strip().lower()
        short = candidate.replace(f"{db}.", "").strip()
        if short not in allowed and candidate not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Table not in allowed list: {payload.locked_table}",
            )
    memory_store.set_table_lock(payload.session_id, payload.locked_table)
    lock = memory_store.get_table_lock(payload.session_id)
    return TableLockResponse(
        session_id=payload.session_id,
        locked_table=lock.locked_table if lock else None,
    )


@app.post("/chat/answer", response_model=ChatAnswerResponse)
def chat_answer(payload: ChatQueryRequest) -> ChatAnswerResponse:
    rag_config = (
        memory_store.get_rag_config(payload.session_id)
        if payload.session_id
        else None
    )

    try:
        if rag_config is not None and rag_config.enabled and rag_config.collection_name:
            response_payload = _run_rag_chat_flow(payload)
        else:
            response_payload = _run_chat_flow(payload)
    except (ValueError, SQLValidationError, SQLExecutionError, GuardrailsServiceError):
        fallback_answer = build_processing_fallback_answer(payload.question)
        if payload.session_id:
            memory_store.append_user_message(payload.session_id, payload.question)
            memory_store.append_assistant_message(payload.session_id, fallback_answer)
            memory_store.set_last_answer(payload.session_id, fallback_answer)
            memory_store.set_last_intent(payload.session_id, "fallback")

        response_payload = {
            "session_id": payload.session_id,
            "original_question": payload.question,
            "answer": fallback_answer,
            "mode": "fallback",
            "sources": [],
            "metadata": {},
            "visualization": None,
        }
    except Exception:
        fallback_answer = build_processing_fallback_answer(payload.question)
        if payload.session_id:
            memory_store.append_user_message(payload.session_id, payload.question)
            memory_store.append_assistant_message(payload.session_id, fallback_answer)
            memory_store.set_last_answer(payload.session_id, fallback_answer)
            memory_store.set_last_intent(payload.session_id, "fallback")

        response_payload = {
            "session_id": payload.session_id,
            "original_question": payload.question,
            "answer": fallback_answer,
            "mode": "fallback",
            "sources": [],
            "metadata": {},
            "visualization": None,
        }

    _log_chat_response(endpoint="/chat/answer", payload=payload, response_payload=response_payload)
    return ChatAnswerResponse(
        session_id=response_payload["session_id"],
        original_question=response_payload["original_question"],
        answer=response_payload["answer"],
        mode=response_payload.get("mode"),
        sources=response_payload.get("sources", []),
        metadata=response_payload.get("metadata", {}),
        visualization=response_payload.get("visualization"),
    )
