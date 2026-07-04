"""Local user account and token-usage persistence for Easy Research."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from datetime import datetime
from pathlib import Path

from src.config import AUTH_DIR, BASE_VECTOR_DIR


USERS_FILE = AUTH_DIR / "users.json"
USAGE_FILE = AUTH_DIR / "usage.json"
WORKSPACE_ROOT = BASE_VECTOR_DIR / "users"


def _read_json(path: Path, default):
    """Read a JSON file, returning the provided default when missing."""
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, data) -> None:
    """Persist JSON data with stable indentation for easier inspection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def slugify_user(username: str) -> str:
    """Convert a username into a filesystem-safe user key."""
    value = re.sub(r"[^a-z0-9]+", "_", (username or "").strip().lower())
    return value.strip("_") or "user"


def _hash_password(password: str, salt: str) -> str:
    """Hash a password with PBKDF2-HMAC using a per-user salt."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        120000,
    ).hex()


def _public_user_record(record: dict) -> dict:
    """Return only the fields safe to expose back to the UI."""
    return {
        "username": record["username"],
        "user_slug": record["user_slug"],
        "created_at": record["created_at"],
        "has_groq_api_key": bool(record.get("groq_api_key")),
    }


def list_users() -> dict:
    """Load all stored user accounts."""
    return _read_json(USERS_FILE, {})


def register_user(username: str, password: str) -> dict:
    """Create a new local account for the app."""
    normalized_name = (username or "").strip()
    if not normalized_name:
        raise ValueError("Username is required.")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")

    users = list_users()
    lookup_key = normalized_name.lower()
    if lookup_key in users:
        raise ValueError("An account with that username already exists.")

    salt = secrets.token_hex(16)
    record = {
        "username": normalized_name,
        "user_slug": slugify_user(normalized_name),
        "password_salt": salt,
        "password_hash": _hash_password(password, salt),
        "groq_api_key": "",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    users[lookup_key] = record
    _write_json(USERS_FILE, users)
    return _public_user_record(record)


def authenticate_user(username: str, password: str) -> dict:
    """Validate credentials and return the public account payload."""
    users = list_users()
    lookup_key = (username or "").strip().lower()
    record = users.get(lookup_key)
    if not record:
        raise ValueError("Invalid username or password.")

    actual_hash = _hash_password(password, record["password_salt"])
    if not hmac.compare_digest(record["password_hash"], actual_hash):
        raise ValueError("Invalid username or password.")

    return _public_user_record(record)


def get_user_groq_key(username: str) -> str:
    """Return the saved Groq API key for the account when available."""
    users = list_users()
    record = users.get((username or "").strip().lower(), {})
    return record.get("groq_api_key", "")


def save_user_groq_key(username: str, api_key: str) -> None:
    """Store or replace the Groq API key for the given user."""
    users = list_users()
    lookup_key = (username or "").strip().lower()
    if lookup_key not in users:
        raise ValueError("Account not found.")

    users[lookup_key]["groq_api_key"] = (api_key or "").strip()
    _write_json(USERS_FILE, users)


def get_user_workspace_root(username: str) -> str:
    """Return the dedicated workspace root for the active user."""
    workspace_root = WORKSPACE_ROOT / slugify_user(username)
    workspace_root.mkdir(parents=True, exist_ok=True)
    return str(workspace_root)


def get_usage_summary(username: str) -> dict:
    """Return accumulated token usage metrics for the current user."""
    usage_store = _read_json(USAGE_FILE, {})
    usage = usage_store.get(slugify_user(username), {})
    return {
        "total_prompt_tokens": int(usage.get("total_prompt_tokens", 0)),
        "total_completion_tokens": int(usage.get("total_completion_tokens", 0)),
        "total_tokens": int(usage.get("total_tokens", 0)),
        "requests": int(usage.get("requests", 0)),
        "last_updated": usage.get("last_updated", ""),
    }


def record_token_usage(username: str, usage: dict) -> None:
    """Accumulate request and token counts for the given user."""
    if not usage:
        return

    usage_store = _read_json(USAGE_FILE, {})
    usage_key = slugify_user(username)
    current = usage_store.get(usage_key, {})

    prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)
    total_tokens = int(usage.get("total_tokens", 0) or 0)

    current["total_prompt_tokens"] = int(current.get("total_prompt_tokens", 0)) + prompt_tokens
    current["total_completion_tokens"] = int(current.get("total_completion_tokens", 0)) + completion_tokens
    current["total_tokens"] = int(current.get("total_tokens", 0)) + total_tokens
    current["requests"] = int(current.get("requests", 0)) + 1
    current["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    usage_store[usage_key] = current
    _write_json(USAGE_FILE, usage_store)
