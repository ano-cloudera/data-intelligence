from __future__ import annotations

import html
import json
import re
from urllib.parse import urljoin

import httpx

from app.core.config import Settings, get_settings
from app.schemas.rag import (
    RagKnowledgeBaseOption,
    RagModelOption,
    RagSessionConfigRequest,
)
from app.schemas.sql import AnswerSource


class RagClientError(RuntimeError):
    pass


_RAG_CITATION_PATTERN = re.compile(r"<a\b[^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_HTML_TAG_PATTERN = re.compile(r"</?[^>]+>")


class RagClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _build_url(self, path: str) -> str:
        base = self.settings.rag_base_url.rstrip("/") + "/"
        return urljoin(base, path.lstrip("/"))

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=self.settings.rag_timeout_seconds)

    def _parse_model_options(self, path: str) -> list[RagModelOption]:
        with self._client() as client:
            response = client.get(self._build_url(path), headers={"accept": "application/json"})
            response.raise_for_status()
            payload = response.json()

        return [
            RagModelOption(
                model_id=item["model_id"],
                name=item["name"],
                available=item.get("available", True),
                replica_count=item.get("replica_count") or 0,
                tool_calling_supported=bool(item.get("tool_calling_supported", False)),
            )
            for item in payload
            if item.get("available", True)
        ]

    def get_chat_models(self) -> list[RagModelOption]:
        return self._parse_model_options("/llm-service/models/llm")

    def get_rerank_models(self) -> list[RagModelOption]:
        return self._parse_model_options("/llm-service/models/reranking")

    def get_model_source(self) -> str | None:
        with self._client() as client:
            response = client.get(
                self._build_url("/llm-service/models/model_source"),
                headers={"accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        return payload if isinstance(payload, str) else None

    def get_knowledge_bases(self) -> list[RagKnowledgeBaseOption]:
        with self._client() as client:
            response = client.get(
                self._build_url("/api/v1/rag/dataSources"),
                headers={"accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()

        knowledge_bases: list[RagKnowledgeBaseOption] = []
        for item in payload:
            knowledge_bases.append(
                RagKnowledgeBaseOption(
                    id=item["id"],
                    name=item["name"],
                    description=item.get("description"),
                    document_count=item.get("documentCount") or 0,
                    embedding_model=item.get("embeddingModel"),
                    summarization_model=item.get("summarizationModel"),
                    metadata={
                        key: value
                        for key, value in item.items()
                        if key
                        not in {
                            "id",
                            "name",
                            "description",
                            "documentCount",
                            "embeddingModel",
                            "summarizationModel",
                        }
                    },
                )
            )

        return knowledge_bases

    def create_session(self, payload: RagSessionConfigRequest) -> int:
        request_body = {
            "name": payload.session_name,
            "dataSourceIds": [payload.knowledge_base_id],
            "projectId": payload.project_id,
            "inferenceModel": payload.inference_model_id,
            "rerankModel": payload.rerank_model_id,
            "responseChunks": payload.response_chunks,
            "queryConfiguration": {
                "enableHyde": payload.query_configuration.enable_hyde,
                "enableSummaryFilter": payload.query_configuration.enable_summary_filter,
                "enableToolCalling": payload.query_configuration.enable_tool_calling,
                "disableStreaming": payload.query_configuration.disable_streaming,
                "selectedTools": payload.query_configuration.selected_tools,
            },
        }

        with self._client() as client:
            response = client.post(
                self._build_url("/api/v1/rag/sessions"),
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            response.raise_for_status()
            created = response.json()

        session_id = created.get("id")
        if not isinstance(session_id, int):
            raise RagClientError("RAG session creation did not return a valid session ID.")
        return session_id

    def stream_completion(self, session_id: int, question: str) -> dict[str, str | None]:
        payload = {
            "query": question,
            "configuration": {
                "exclude_knowledge_base": False,
                "use_question_condensing": False,
            },
        }
        chunks: list[str] = []
        response_id: str | None = None

        with self._client() as client:
            with client.stream(
                "POST",
                self._build_url(f"/llm-service/sessions/{session_id}/stream-completion"),
                headers={
                    "accept": "text/event-stream",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if not data:
                        continue

                    try:
                        payload_item = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    if isinstance(payload_item, dict):
                        text = payload_item.get("text")
                        if isinstance(text, str):
                            chunks.append(text)
                        if isinstance(payload_item.get("response_id"), str):
                            response_id = payload_item["response_id"]

        answer = "".join(chunks).strip()
        if not answer:
            raise RagClientError("RAG stream completion returned no answer text.")

        return {
            "answer": self.sanitize_answer_text(answer),
            "response_id": response_id,
        }

    def get_sources(
        self,
        session_id: int,
        response_id: str | None = None,
        data_source_id: int | None = None,
    ) -> list[AnswerSource]:
        with self._client() as client:
            response = client.get(
                self._build_url(f"/llm-service/sessions/{session_id}/chat-history"),
                headers={"accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()

        items = payload.get("data", []) if isinstance(payload, dict) else []
        if not isinstance(items, list):
            return []

        candidate: dict | None = None
        if response_id:
            for item in reversed(items):
                if isinstance(item, dict) and item.get("id") == response_id:
                    candidate = item
                    break

        if candidate is None:
            for item in reversed(items):
                if isinstance(item, dict) and item.get("source_nodes"):
                    candidate = item
                    break

        if not isinstance(candidate, dict):
            return []

        source_nodes = candidate.get("source_nodes", [])
        if not isinstance(source_nodes, list):
            return []

        seen: set[tuple[str | None, str | None]] = set()
        sources: list[AnswerSource] = []
        for node in source_nodes:
            if not isinstance(node, dict):
                continue

            title = node.get("source_file_name") or node.get("doc_id") or node.get("node_id")
            if not isinstance(title, str) or not title:
                continue

            document_id = node.get("doc_id") if isinstance(node.get("doc_id"), str) else None
            node_id = node.get("node_id") if isinstance(node.get("node_id"), str) else None
            score = node.get("score")
            score_value = float(score) if isinstance(score, (int, float)) else None

            dedupe_key = (document_id, node_id)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            preview_url = None
            if data_source_id is not None and document_id:
                preview_url = self._build_url(
                    f"/api/v1/rag/dataSources/{data_source_id}/files/{document_id}/download"
                )

            sources.append(
                AnswerSource(
                    title=title,
                    document_id=document_id,
                    node_id=node_id,
                    score=score_value,
                    preview_url=preview_url,
                    download_url=preview_url,
                )
            )

        return sources

    @staticmethod
    def sanitize_answer_text(answer: str) -> str:
        cleaned = _RAG_CITATION_PATTERN.sub(lambda match: html.unescape(match.group(1).strip()), answer)
        cleaned = _HTML_TAG_PATTERN.sub("", cleaned)
        cleaned = html.unescape(cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()
