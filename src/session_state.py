"""Streamlit session-state helpers used across the application."""

import streamlit as st


def initialize_session_state():
    """Seed every session key the app expects before rendering UI."""

    defaults = {
        "reset_counter": 0,
        "db_mode_selected": False,
        "active_db_name": None,
        "active_topic_folder": None,
        "qa_history": [],
        "all_chunks": [],
        "successful_documents": [],
        "is_authenticated": False,
        "current_username": None,
        "user_has_api_key": False,
        "user_groq_api_key": "",
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def widget_key(name: str) -> str:
    """Return a reset-aware widget key so fields can be recreated cleanly."""
    return f"{name}_{st.session_state['reset_counter']}"


def reset_loaded_data():
    """Clear the active workspace session and its associated widget state."""

    keys_to_clear = [
        "all_chunks",
        "successful_documents",
        "query",
        "dataset_id",
        "existing_chunk_count",
        "vector_store",
        "selected_history",
        "retrieved_chunks",
        "active_topic_folder",
        "active_db_name",
        "db_mode_selected",
        "qa_history",
        "recent_answers",
        "is_authenticated",
        "current_username",
        "user_has_api_key",
        "user_groq_api_key",
        "source_input_value",
    ]

    widget_prefixes_to_clear = [
        "research_name",
        "source_input",
        "google_num_results",
        "file_uploader",
        "answer_question",
        "answer_top_k",
        "load_data_btn",
        "clear_current_session_btn",
        "generate_answer_btn",
    ]

    for key in list(st.session_state.keys()):
        if key in keys_to_clear or any(
            key.startswith(prefix) for prefix in widget_prefixes_to_clear
        ):
            del st.session_state[key]

    st.session_state["reset_counter"] = st.session_state.get("reset_counter", 0) + 1


def reset_input_fields_only():
    """Reset only source-input widgets while preserving the current workspace."""

    widget_prefixes_to_clear = [
        "source_input",
        "google_num_results",
        "file_uploader",
    ]

    for key in list(st.session_state.keys()):
        if any(key.startswith(prefix) for prefix in widget_prefixes_to_clear):
            del st.session_state[key]

    st.session_state["reset_counter"] = st.session_state.get("reset_counter", 0) + 1
