"""Persistence helpers for per-workspace chat history."""

import os
import json
from datetime import datetime


CHAT_HISTORY_FILE = "chat_history.json"


def get_chat_history_path(folder_path: str) -> str:
    """Return the chat history file path inside a workspace folder."""
    return os.path.join(folder_path, CHAT_HISTORY_FILE)


def load_chat_history(folder_path: str) -> list:
    """Load saved chat history for a workspace, falling back to an empty list."""
    if not folder_path:
        return []

    history_path = get_chat_history_path(folder_path)

    if not os.path.exists(history_path):
        return []

    try:
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_chat_history(folder_path: str, chat_history: list):
    """Persist the full chat history for a workspace."""
    if not folder_path:
        return

    os.makedirs(folder_path, exist_ok=True)

    history_path = get_chat_history_path(folder_path)

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(chat_history, f, indent=4, ensure_ascii=False)


def append_chat_message(folder_path: str, question: str, answer: str) -> list:
    """Append one generated Q&A pair and return the updated history payload."""
    chat_history = load_chat_history(folder_path)

    chat_history.append({
        "question": question,
        "answer": answer,
        "time": datetime.now().strftime("%d.%m.%Y - %I:%M %p"),
    })

    save_chat_history(folder_path, chat_history)

    return chat_history


def clear_chat_history(folder_path: str):
    """Remove all saved messages for a workspace while keeping the file in place."""
    save_chat_history(folder_path, [])
