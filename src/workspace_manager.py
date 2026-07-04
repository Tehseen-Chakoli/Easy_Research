"""Workspace orchestration helpers for the Streamlit app layer."""

from __future__ import annotations

import uuid
from datetime import datetime

import streamlit as st

from src.chat_history_manager import load_chat_history
from src.document_processor import process_extracted_content
from src.history_manager import list_research_history
from src.user_manager import get_user_workspace_root


def add_source_metadata_to_chunks(chunks, source_id: str, source_type: str, dataset_id: str):
    """Attach source metadata to every chunk generated from one source item."""
    for chunk in chunks:
        chunk.metadata["source_id"] = source_id
        chunk.metadata["source_type"] = source_type
        chunk.metadata["dataset_id"] = dataset_id
    return chunks


def process_extracted_item_into_chunks(extracted_item: dict, source_type: str, dataset_id: str):
    """Convert one extracted source into chunks and stamp it with stable metadata."""
    source_id = str(uuid.uuid4())[:8]
    chunks = process_extracted_content(extracted_item)
    chunks = add_source_metadata_to_chunks(
        chunks=chunks,
        source_id=source_id,
        source_type=source_type,
        dataset_id=dataset_id,
    )
    extracted_item["source_id"] = source_id
    extracted_item["source_type"] = source_type
    extracted_item["dataset_id"] = dataset_id
    return chunks, extracted_item


def get_current_workspace_root() -> str | None:
    """Resolve the active user's workspace root directory from session state."""
    username = st.session_state.get("current_username")
    if not username:
        return None
    return get_user_workspace_root(username)


def history_sort_key(item: dict) -> datetime:
    """Return the best available timestamp for sorting saved workspaces."""
    candidates = [
        item.get("updated_at"),
        item.get("created_at"),
    ]
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y - %I:%M %p",
    ]

    for value in candidates:
        if value:
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

    topic = item.get("topic", "")
    if "|" in topic:
        try:
            date_part = topic.split("|")[-1].strip()
            return datetime.strptime(date_part, "%d.%m.%Y - %I:%M %p")
        except ValueError:
            pass

    return datetime.min


def get_sorted_history() -> list[dict]:
    """Load saved research workspaces ordered from newest to oldest."""
    history = list_research_history(base_dir=get_current_workspace_root())
    return sorted(history, key=history_sort_key, reverse=True)


def restore_workspace_session(selected_workspace: dict, vector_store) -> None:
    """Hydrate session state so a saved workspace can be reopened seamlessly."""
    sources = selected_workspace.get("sources", [])

    st.session_state["vector_store"] = vector_store
    st.session_state["active_db_name"] = selected_workspace["topic"]
    st.session_state["query"] = selected_workspace["topic"]
    st.session_state["active_topic_folder"] = selected_workspace["folder_path"]
    st.session_state["qa_history"] = load_chat_history(selected_workspace["folder_path"])
    st.session_state["dataset_id"] = selected_workspace.get("dataset_id") or str(uuid.uuid4())[:8]
    st.session_state["created_at"] = (
        selected_workspace.get("created_at")
        or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    st.session_state["successful_documents"] = sources
    st.session_state["all_chunks"] = []
    st.session_state["existing_chunk_count"] = int(selected_workspace.get("total_chunks", 0) or 0)
    st.session_state["db_mode_selected"] = True
