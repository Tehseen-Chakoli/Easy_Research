"""Chat history persistence for saved research workspaces."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


CHAT_HISTORY_FILE = "chat_history.json"


def get_chat_history_path(folder_path: str) -> Path:
    """Build the chat-history file path for a workspace folder."""
    return Path(folder_path) / CHAT_HISTORY_FILE


def load_chat_history(folder_path: str) -> list[dict]:
    """Load saved question-answer history for a workspace."""
    if not folder_path:
        return []

    history_path = get_chat_history_path(folder_path)
    if not history_path.exists():
        return []

    with open(history_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_chat_history(folder_path: str, chat_history: list[dict]) -> None:
    """Persist the full chat history payload for a workspace."""
    history_path = get_chat_history_path(folder_path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as file:
        json.dump(chat_history, file, indent=2, ensure_ascii=False)


def append_chat_message(folder_path: str, question: str, answer: str) -> list[dict]:
    """Append one Q&A record and return the updated history list."""
    chat_history = load_chat_history(folder_path)
    chat_history.append(
        {
            "question": question,
            "answer": answer,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    save_chat_history(folder_path, chat_history)
    return chat_history
