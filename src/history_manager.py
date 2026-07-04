"""Workspace metadata and persistence helpers for Easy Research."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from src.config import BASE_VECTOR_DIR


def slugify_topic(topic: str) -> str:
    """Convert a workspace name into a filesystem-safe slug."""
    normalized = re.sub(r"[^a-z0-9]+", "_", (topic or "").strip().lower())
    return normalized.strip("_") or "research_workspace"


def create_topic_folder(topic: str, base_dir: str | None = None) -> str:
    """Create a timestamped folder for a persisted research workspace."""
    target_root = Path(base_dir) if base_dir else BASE_VECTOR_DIR
    target_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    folder_name = f"{slugify_topic(topic)}_{timestamp}"
    folder_path = target_root / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)
    return str(folder_path)


def save_metadata(folder_path: str, metadata: dict) -> None:
    """Persist workspace metadata alongside the stored vector index."""
    metadata_path = Path(folder_path) / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)


def load_metadata(folder_path: str) -> dict:
    """Load metadata for a stored workspace when it exists."""
    metadata_path = Path(folder_path) / "metadata.json"
    if not metadata_path.exists():
        return {}

    with open(metadata_path, "r", encoding="utf-8") as file:
        return json.load(file)


def list_research_history(base_dir: str | None = None) -> list[dict]:
    """Return saved workspaces ordered from newest to oldest."""
    target_root = Path(base_dir) if base_dir else BASE_VECTOR_DIR
    if not target_root.exists():
        return []

    history = []
    for folder_name in os.listdir(target_root):
        folder_path = target_root / folder_name
        if not folder_path.is_dir():
            continue

        metadata = load_metadata(str(folder_path))
        history.append(
            {
                "folder_name": folder_name,
                "folder_path": str(folder_path),
                "topic": metadata.get("topic", folder_name),
                "created_at": metadata.get("created_at", ""),
                "total_chunks": metadata.get("total_chunks", 0),
                "total_sources": metadata.get("total_sources", 0),
                "source_url": metadata.get("source_url", ""),
                "sources": metadata.get("sources", []),
            }
        )

    return sorted(history, key=lambda item: item.get("created_at", ""), reverse=True)
