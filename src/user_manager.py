"""User account, credential, API-key, and usage persistence helpers."""

import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import datetime


AUTH_DIR = os.path.join("config", "auth")
USERS_FILE = os.path.join(AUTH_DIR, "users.json")
USAGE_FILE = os.path.join(AUTH_DIR, "usage.json")
WORKSPACE_ROOT = os.path.join("vector_store", "users")


def _ensure_parent(path: str):
    """Create the parent directory for a managed JSON file if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _read_json(path: str, default):
    """Read JSON from disk, falling back to the provided default payload."""
    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: str, data):
    """Persist JSON using UTF-8 and stable indentation for easier inspection."""
    _ensure_parent(path)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def slugify_user(username: str) -> str:
    """Convert a username into a safe directory key."""
    value = (username or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value or "user"


def _hash_password(password: str, salt: str) -> str:
    """Hash a password with PBKDF2-HMAC using the stored per-user salt."""
    password_bytes = password.encode("utf-8")
    salt_bytes = bytes.fromhex(salt)
    return hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt_bytes,
        120000,
    ).hex()


def _public_user_record(record: dict) -> dict:
    """Return only the account fields that are safe for the UI layer."""
    return {
        "username": record["username"],
        "user_slug": record["user_slug"],
        "created_at": record["created_at"],
        "has_groq_api_key": bool(record.get("groq_api_key")),
    }


def list_users() -> dict:
    """Load all persisted user records."""
    return _read_json(USERS_FILE, {})


def register_user(username: str, password: str) -> dict:
    """Create a new account after validating the submitted credentials."""
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
    """Validate login credentials and return the safe public user payload."""
    users = list_users()
    lookup_key = (username or "").strip().lower()
    record = users.get(lookup_key)
    if not record:
        raise ValueError("Invalid username or password.")

    expected_hash = record["password_hash"]
    actual_hash = _hash_password(password, record["password_salt"])
    if not hmac.compare_digest(expected_hash, actual_hash):
        raise ValueError("Invalid username or password.")

    return _public_user_record(record)


def get_user_record(username: str) -> dict | None:
    """Look up a public account record by username."""
    users = list_users()
    record = users.get((username or "").strip().lower())
    if not record:
        return None
    return _public_user_record(record)


def get_user_groq_key(username: str) -> str:
    """Return the saved Groq API key for the given user, if present."""
    users = list_users()
    record = users.get((username or "").strip().lower(), {})
    return record.get("groq_api_key", "")


def save_user_groq_key(username: str, api_key: str):
    """Store or replace the Groq API key associated with an account."""
    normalized_username = (username or "").strip().lower()
    users = list_users()
    if normalized_username not in users:
        raise ValueError("Account not found.")

    users[normalized_username]["groq_api_key"] = (api_key or "").strip()
    _write_json(USERS_FILE, users)


def get_user_workspace_root(username: str) -> str:
    """Return the on-disk workspace root for a specific user account."""
    user_slug = slugify_user(username)
    workspace_root = os.path.join(WORKSPACE_ROOT, user_slug)
    os.makedirs(workspace_root, exist_ok=True)
    return workspace_root


def get_usage_summary(username: str) -> dict:
    """Aggregate the persisted token-usage metrics for one user."""
    usage_store = _read_json(USAGE_FILE, {})
    user_usage = usage_store.get(slugify_user(username), {})
    return {
        "total_prompt_tokens": int(user_usage.get("total_prompt_tokens", 0)),
        "total_completion_tokens": int(user_usage.get("total_completion_tokens", 0)),
        "total_tokens": int(user_usage.get("total_tokens", 0)),
        "requests": int(user_usage.get("requests", 0)),
        "last_updated": user_usage.get("last_updated"),
    }


def record_token_usage(username: str, usage: dict):
    """Accumulate prompt, completion, and total token usage for a user."""
    if not usage:
        return

    usage_store = _read_json(USAGE_FILE, {})
    user_key = slugify_user(username)
    user_usage = usage_store.get(user_key, {})

    prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)
    total_tokens = int(usage.get("total_tokens", 0) or 0)

    user_usage["total_prompt_tokens"] = int(user_usage.get("total_prompt_tokens", 0)) + prompt_tokens
    user_usage["total_completion_tokens"] = int(user_usage.get("total_completion_tokens", 0)) + completion_tokens
    user_usage["total_tokens"] = int(user_usage.get("total_tokens", 0)) + total_tokens
    user_usage["requests"] = int(user_usage.get("requests", 0)) + 1
    user_usage["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    usage_store[user_key] = user_usage
    _write_json(USAGE_FILE, usage_store)
