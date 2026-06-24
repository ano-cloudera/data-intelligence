from __future__ import annotations

import sys
try:
    import pysqlite3  # type: ignore
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

from app.config import settings

_client: chromadb.PersistentClient | None = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def _embedding_fn() -> OllamaEmbeddingFunction:
    return OllamaEmbeddingFunction(
        model_name=settings.embed_model,
        url=f"{settings.ollama_base_url}/api/embeddings",
    )


def search_documents(query: str, collection_name: str, top_k: int = 5) -> list[dict]:
    client = _get_client()
    collection = client.get_collection(
        name=collection_name,
        embedding_function=_embedding_fn(),
    )
    results = collection.query(query_texts=[query], n_results=top_k)

    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    output = []
    for doc, meta, dist in zip(docs, metadatas, distances):
        score = round(1 - dist, 4) if dist is not None else None
        output.append({
            "document_id": meta.get("source", ""),
            "title": f"{meta.get('source', '')} (halaman {meta.get('page', '?')})",
            "excerpt": doc[:400] if doc else "",
            "score": score,
        })
    return output
