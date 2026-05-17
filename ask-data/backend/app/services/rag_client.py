from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.sql import AnswerSource


class RagClientError(RuntimeError):
    pass


class ChromaRagClient:
    """
    ChromaDB-backed RAG client.
    Embeds documents using Ollama (nomic-embed-text) or sentence-transformers fallback.
    Persists the vector store to CHROMA_PERSIST_DIR (default: ./chroma_db).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: Any = None
        self._ef: Any = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        from app.compat import patch_sqlite
        patch_sqlite()
        import chromadb
        persist_dir = self.settings.chroma_persist_dir
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        return self._client

    def _get_embedding_function(self) -> Any:
        if self._ef is not None:
            return self._ef
        try:
            from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
            self._ef = OllamaEmbeddingFunction(
                url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                model_name=os.getenv("EMBED_MODEL", "nomic-embed-text"),
            )
        except Exception:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            self._ef = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        return self._ef

    # ── Collections ──────────────────────────────────────────────────────────

    def list_collections(self) -> list[dict[str, Any]]:
        client = self._get_client()
        collections = client.list_collections()
        return [
            {
                "name": col.name,
                "document_count": col.count(),
            }
            for col in collections
        ]

    def get_or_create_collection(self, name: str) -> Any:
        client = self._get_client()
        ef = self._get_embedding_function()
        return client.get_or_create_collection(
            name=name,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Ingest ───────────────────────────────────────────────────────────────

    def ingest_texts(
        self,
        collection_name: str,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> int:
        collection = self.get_or_create_collection(collection_name)
        _ids = ids or [f"doc_{i}" for i in range(len(texts))]
        _meta = metadatas or [{} for _ in texts]
        collection.add(documents=texts, metadatas=_meta, ids=_ids)
        return len(texts)

    def ingest_pdf(self, collection_name: str, pdf_path: str) -> int:
        try:
            import pypdf
        except ImportError as exc:
            raise RagClientError("pypdf is required for PDF ingestion: pip install pypdf") from exc

        path = Path(pdf_path)
        if not path.exists():
            raise RagClientError(f"PDF not found: {pdf_path}")

        # Copy PDF into rag_pdf_dir so it can be served later
        pdf_dir = Path(self.settings.rag_pdf_dir)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        dest = pdf_dir / path.name
        if not dest.exists() or dest.resolve() != path.resolve():
            shutil.copy2(str(path), str(dest))

        reader = pypdf.PdfReader(str(path))
        texts: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                continue
            chunk_id = f"{path.stem}_p{i+1}"
            texts.append(text)
            metadatas.append({"source": path.name, "page": i + 1, "pdf_filename": path.name})
            ids.append(chunk_id)

        if not texts:
            raise RagClientError(f"No extractable text found in {pdf_path}")

        return self.ingest_texts(collection_name, texts, metadatas, ids)

    # ── Query ─────────────────────────────────────────────────────────────────

    def _get_sentence_transformer_ef(self) -> Any:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        return SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    def query(
        self,
        collection_name: str,
        question: str,
        top_k: int = 5,
    ) -> list[AnswerSource]:
        client = self._get_client()
        try:
            collection = client.get_collection(
                name=collection_name,
                embedding_function=self._get_embedding_function(),
            )
        except Exception as exc:
            raise RagClientError(f"Collection '{collection_name}' not found: {exc}") from exc

        try:
            results = collection.query(
                query_texts=[question],
                n_results=min(top_k, collection.count()),
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            # Ollama embedding failed — retry with SentenceTransformer
            collection = client.get_collection(
                name=collection_name,
                embedding_function=self._get_sentence_transformer_ef(),
            )
            results = collection.query(
                query_texts=[question],
                n_results=min(top_k, collection.count()),
                include=["documents", "metadatas", "distances"],
            )

        sources: list[AnswerSource] = []
        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            score = round(1.0 - float(dist), 4)
            pdf_filename = meta.get("pdf_filename") or meta.get("source")
            title = meta.get("source", collection_name)
            page = meta.get("page")
            if page:
                title = f"{title} (halaman {page})"
            preview_url = (
                f"/api/backend/rag/documents/{pdf_filename}" if pdf_filename else None
            )
            download_url = (
                f"/api/backend/rag/documents/{pdf_filename}?download=true" if pdf_filename else None
            )
            sources.append(
                AnswerSource(
                    title=title,
                    document_id=pdf_filename,
                    node_id=None,
                    score=score,
                    preview_url=preview_url,
                    download_url=download_url,
                    excerpt=doc[:600] if doc else None,
                )
            )

        return sources

    def build_context_text(self, sources: list[AnswerSource]) -> str:
        if not sources:
            return ""
        parts = []
        for i, src in enumerate(sources, 1):
            parts.append(f"[{i}] {src.title}\n{src.excerpt or ''}")
        return "\n\n".join(parts)

    # ── Health ────────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        try:
            client = self._get_client()
            cols = client.list_collections()
            return {
                "status": "ok",
                "collections": len(cols),
                "persist_dir": self.settings.chroma_persist_dir,
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}
