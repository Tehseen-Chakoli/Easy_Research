"""Persistence helpers for saved research workspaces and metadata."""

import os
import re
import json
from datetime import datetime
import shutil


BASE_VECTOR_DIR = "vector_store"


def get_base_vector_dir(base_dir: str | None = None) -> str:
    """Resolve the root directory that stores workspace vector data."""
    return os.path.abspath(base_dir or BASE_VECTOR_DIR)


def slugify_topic(topic: str) -> str:
    """Create a filesystem-safe workspace slug while keeping names readable."""
    topic = topic.lower().strip()
    topic = re.sub(r"[^a-z0-9]+", "_", topic)
    topic = topic.strip("_")
    return topic[:60] or "research_workspace"


def create_topic_folder(topic: str, base_dir: str | None = None) -> str:
    """Create a timestamped folder for a newly saved research workspace."""
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    safe_topic = slugify_topic(topic)

    folder_name = f"{safe_topic}_{timestamp}"
    folder_path = os.path.join(base_dir or BASE_VECTOR_DIR, folder_name)

    os.makedirs(folder_path, exist_ok=True)

    return folder_path


def _resolve_database_folder(folder_path: str, base_dir: str | None = None) -> str:
    """Validate that a workspace folder stays inside the configured storage root."""
    resolved_folder = os.path.abspath(folder_path)
    resolved_base_dir = get_base_vector_dir(base_dir)

    if os.path.commonpath([resolved_base_dir, resolved_folder]) != resolved_base_dir:
        raise ValueError("Database folder must be inside the vector_store directory.")

    return resolved_folder


def save_metadata(folder_path: str, metadata: dict):
    """Write workspace metadata alongside the stored vector database."""
    metadata_path = os.path.join(folder_path, "metadata.json")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)


def load_metadata(folder_path: str):
    """Load workspace metadata, returning an empty payload when absent."""
    metadata_path = os.path.join(folder_path, "metadata.json")

    if not os.path.exists(metadata_path):
        return {}

    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_research_history(base_dir: str | None = None):
    """Return all saved workspaces and their metadata for the current storage root."""
    history_root = base_dir or BASE_VECTOR_DIR

    if not os.path.exists(history_root):
        return []

    history = []

    for folder in os.listdir(history_root):
        folder_path = os.path.join(history_root, folder)

        if os.path.isdir(folder_path):
            metadata = load_metadata(folder_path)

            history.append({
                "folder_name": folder,
                "folder_path": folder_path,
                "topic": metadata.get("topic", folder),
                "dataset_id": metadata.get("dataset_id"),
                "created_at": metadata.get("created_at", ""),
                "updated_at": metadata.get("updated_at", ""),
                "total_chunks": metadata.get("total_chunks", 0),
                "total_sources": metadata.get("total_sources", 0),
                "sources": metadata.get("sources", []),
            })

    history = sorted(
        history,
        key=lambda x: x["created_at"],
        reverse=True
    )

    return history


def delete_research_database(folder_path: str, base_dir: str | None = None) -> bool:
    """Delete a saved workspace after verifying it is inside the allowed root."""

    if not folder_path:
        raise ValueError("No database folder path provided.")

    resolved_folder = _resolve_database_folder(folder_path, base_dir=base_dir)

    if not os.path.exists(resolved_folder):
        raise FileNotFoundError(f"Database folder not found: {folder_path}")

    if not os.path.isdir(resolved_folder):
        raise ValueError(f"Path is not a folder: {folder_path}")

    shutil.rmtree(resolved_folder)

    return True
