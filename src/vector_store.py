"""Embedding and vector-store helpers for Easy Research."""

from __future__ import annotations

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from src.config import EMBEDDING_MODEL_NAME


def get_embedding_model() -> HuggingFaceEmbeddings:
    """Create the embedding model used to index research chunks."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def create_vector_store(chunks) -> FAISS:
    """Build an in-memory FAISS vector store from processed chunks."""
    if not chunks:
        raise ValueError("No chunks were provided for vector store creation.")

    embeddings = get_embedding_model()
    return FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )
