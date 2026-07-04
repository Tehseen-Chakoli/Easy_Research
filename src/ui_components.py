"""Reusable Streamlit UI sections for auth, history, and export flows."""

from __future__ import annotations

import html

import streamlit as st

from src.chat_export import build_chat_history_pdf, slugify_filename
from src.session_state import widget_key
from src.user_manager import (
    authenticate_user,
    get_usage_summary,
    get_user_groq_key,
    register_user,
    save_user_groq_key,
)


def _current_username() -> str | None:
    """Return the signed-in username from session state."""
    return st.session_state.get("current_username")


def render_usage_panel() -> None:
    """Show aggregate token usage for the active account in the sidebar."""
    username = _current_username()
    if not username:
        return

    usage = get_usage_summary(username)
    st.sidebar.markdown("### Usage")
    st.sidebar.metric("Total tokens", usage["total_tokens"])
    st.sidebar.metric("Requests", usage["requests"])
    if usage.get("last_updated"):
        st.sidebar.caption(f"Updated {usage['last_updated']}")


def render_auth_screen() -> None:
    """Render the login and account creation screen."""
    st.markdown(
        """
        <div class="hero-shell">
            <div class="hero-kicker">Secure access</div>
            <div class="hero-title">Easy Answer</div>
            <div class="hero-db">Sign in to your research workspace</div>
            <div class="hero-copy">Create an account or log in to manage your own Groq key, workspace history, and token usage.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sign_in_tab, create_tab = st.tabs(["Sign In", "Create Account"])

    with sign_in_tab:
        with st.container(border=True):
            login_username = st.text_input("Username", key=widget_key("login_username"))
            login_password = st.text_input("Password", type="password", key=widget_key("login_password"))
            if st.button("Sign In", use_container_width=True, key=widget_key("sign_in_btn")):
                try:
                    account = authenticate_user(login_username, login_password)
                    st.session_state["is_authenticated"] = True
                    st.session_state["current_username"] = account["username"]
                    st.session_state["user_has_api_key"] = account["has_groq_api_key"]
                    st.session_state["user_groq_api_key"] = get_user_groq_key(account["username"])
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with create_tab:
        with st.container(border=True):
            new_username = st.text_input("Username", key=widget_key("signup_username"))
            new_password = st.text_input("Password", type="password", key=widget_key("signup_password"))
            if st.button("Create Account", use_container_width=True, key=widget_key("create_account_btn")):
                try:
                    account = register_user(new_username, new_password)
                    st.session_state["is_authenticated"] = True
                    st.session_state["current_username"] = account["username"]
                    st.session_state["user_has_api_key"] = False
                    st.session_state["user_groq_api_key"] = ""
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def render_api_key_setup_screen() -> None:
    """Prompt the signed-in user to save a Groq API key before using the app."""
    username = _current_username()
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-kicker">API setup</div>
            <div class="hero-title">Connect Groq</div>
            <div class="hero-db">{html.escape(username or "Signed-in user")}</div>
            <div class="hero-copy">Add your Groq API key to activate answer generation and track usage under your account.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        api_key_value = st.text_input(
            "Groq API key",
            type="password",
            key=widget_key("groq_api_key_input"),
        )
        st.link_button("Get a Groq API key", "https://console.groq.com/keys", use_container_width=True)
        if st.button("Save API Key", use_container_width=True, key=widget_key("save_groq_key_btn")):
            if not api_key_value.strip():
                st.warning("Please enter a Groq API key.")
            else:
                save_user_groq_key(username, api_key_value.strip())
                st.session_state["user_groq_api_key"] = api_key_value.strip()
                st.session_state["user_has_api_key"] = True
                st.rerun()


def render_chat_card(question: str, answer: str, time_text: str) -> None:
    """Render one saved question-and-answer pair with Markdown preserved."""
    safe_question = html.escape(question or "")
    safe_time = html.escape(time_text or "")

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="chat-card-header">
                <div class="question">Q: {safe_question}</div>
                <div class="time">{safe_time}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(answer or "")


def render_chat_history_list() -> None:
    """Render saved Q&A entries in reverse chronological order."""
    chat_history = st.session_state.get("qa_history", [])
    if not chat_history:
        st.caption("No questions yet. Answers will appear here after you generate them.")
        return

    for item in reversed(chat_history):
        render_chat_card(
            question=item.get("question", ""),
            answer=item.get("answer", ""),
            time_text=item.get("time", ""),
        )


def render_chat_export_controls() -> None:
    """Render PDF export controls for the full chat or a selected subset."""
    chat_history = st.session_state.get("qa_history", [])
    if not chat_history:
        st.caption("No conversation history is available to export yet.")
        return

    workspace_name = st.session_state.get("active_db_name", "research_workspace")
    safe_name = slugify_filename(workspace_name)
    export_scope = st.radio(
        "Export scope",
        ["Entire conversation", "Selected questions and answers"],
        horizontal=True,
        key="export_scope",
    )
    export_theme = st.selectbox(
        "PDF theme",
        options=["Light theme", "Dark theme"],
        key="export_theme",
    )

    selected_history = chat_history
    if export_scope == "Selected questions and answers":
        options = [
            f"{item.get('time', 'Recent')} | {item.get('question', 'Untitled question')[:80]}"
            for item in chat_history
        ]
        selected_labels = st.multiselect(
            "Choose entries to export",
            options=options,
            default=options[:1] if options else [],
            key="export_selected_entries",
        )
        selected_history = [
            item for item, label in zip(chat_history, options) if label in selected_labels
        ]
        if not selected_history:
            st.warning("Please select at least one question and answer to export.")
            return

    selected_theme = "light" if export_theme == "Light theme" else "dark"
    file_suffix = "light" if selected_theme == "light" else "dark"
    pdf_bytes = build_chat_history_pdf(
        selected_history,
        workspace_name=workspace_name,
        theme=selected_theme,
    )

    st.download_button(
        "Download PDF",
        data=pdf_bytes,
        file_name=f"{safe_name}_chat_{file_suffix}.pdf",
        mime="application/pdf",
        use_container_width=True,
        key=widget_key("chat_pdf_download_btn"),
    )


def render_page_hero() -> None:
    """Render the active workspace hero and top-level metrics."""
    active_name = st.session_state.get("active_db_name")
    source_count = len(st.session_state.get("successful_documents", []))
    chunk_count = st.session_state.get("existing_chunk_count", len(st.session_state.get("all_chunks", [])))
    chat_count = len(st.session_state.get("qa_history", []))

    hero_status = "Research workspace ready" if active_name else "Create a research workspace"
    hero_title = "Easy Answer"
    hero_subtitle = (
        "Build a focused research workspace from search results, URLs, PDFs, and TXT files, then ask grounded questions and export the chat as PDF."
    )

    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-kicker">{hero_status}</div>
            <div class="hero-title">{html.escape(hero_title)}</div>
            <div class="hero-db">{html.escape(active_name or "No research workspace selected yet")}</div>
            <div class="hero-copy">{html.escape(hero_subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    with metric_col_1:
        st.metric("Sources", source_count)
    with metric_col_2:
        st.metric("Chunks", chunk_count)
    with metric_col_3:
        st.metric("Messages", chat_count)
