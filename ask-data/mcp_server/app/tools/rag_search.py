from __future__ import annotations

from typing import Any

from app.chroma_client import search_documents
from app.config import settings


def search_policy_documents(
    query: str,
    top_k: int = 5,
    collection_name: str | None = None,
) -> dict[str, Any]:
    """
    MCP Tool: Search Bank Jatim policy documents in ChromaDB.
    Returns relevant document chunks with source info and relevance score.
    """
    collection = collection_name or settings.chroma_collection

    try:
        results = search_documents(query=query, collection_name=collection, top_k=top_k)
        return {
            "query": query,
            "collection": collection,
            "results": results,
            "result_count": len(results),
        }
    except Exception as exc:
        return {"error": str(exc), "query": query}
