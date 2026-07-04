"""Chunk retrieval helpers for the Easy Research RAG flow."""

from __future__ import annotations


def retrieve_relevant_chunks(vector_store, question: str, k: int = 4) -> list[dict]:
    """Retrieve the top matching chunks and normalize them for prompt use."""
    if vector_store is None:
        raise ValueError("Vector store is not available.")

    normalized_question = (question or "").strip()
    if not normalized_question:
        raise ValueError("Question cannot be empty.")

    results = vector_store.similarity_search(normalized_question, k=int(k))
    return [
        {
            "content": document.page_content,
            "title": document.metadata.get("title", ""),
            "url": document.metadata.get("url", ""),
            "snippet": document.metadata.get("snippet", ""),
            "extraction_method": document.metadata.get("extraction_method", ""),
        }
        for document in results
    ]
