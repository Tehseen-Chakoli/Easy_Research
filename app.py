"""Easy Research application shell with auth, user-scoped workspaces, and RAG flow."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.answer_generator import generate_answer_with_usage
from src.chat_history_manager import append_chat_message, load_chat_history
from src.chat_export import build_chat_history_pdf, slugify_filename
from src.config import (
    APP_TITLE,
    DEFAULT_NUM_RESULTS,
    DEFAULT_RETRIEVAL_K,
    EMBEDDING_MODEL_NAME,
    GROQ_MODEL,
    SERPER_API_KEY,
)
from src.document_processor import process_extracted_content
from src.file_ingestor import create_extracted_item_from_file
from src.history_manager import create_topic_folder, list_research_history, save_metadata
from src.input_parser import extract_urls_and_queries, is_youtube_url
from src.retriever import retrieve_relevant_chunks
from src.serper_search import search_serper
from src.user_manager import (
    authenticate_user,
    get_usage_summary,
    get_user_groq_key,
    get_user_workspace_root,
    record_token_usage,
    register_user,
    save_user_groq_key,
)
from src.vector_store import create_and_save_vector_store, load_vector_store
from src.web_extractor import extract_content
from src.youtube_loader import create_extracted_item_from_youtube


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="ER",
    layout="wide",
)


def initialize_session_state() -> None:
    """Seed the state fields the app needs across auth, build, and ask flows."""
    defaults = {
        "vector_store_ready": False,
        "vector_store": None,
        "retrieved_chunks": [],
        "generated_answer": "",
        "active_workspace_path": "",
        "active_workspace_name": "",
        "qa_history": [],
        "successful_documents": [],
        "all_chunks": [],
        "is_authenticated": False,
        "current_username": "",
        "user_has_api_key": False,
        "user_groq_api_key": "",
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def reset_answer_state() -> None:
    """Clear answer-oriented state after a workspace is rebuilt or switched."""
    st.session_state["retrieved_chunks"] = []
    st.session_state["generated_answer"] = ""


def current_username() -> str:
    """Return the active username from session state."""
    return st.session_state.get("current_username", "")


def current_workspace_root() -> str:
    """Resolve the authenticated user's dedicated workspace root."""
    return get_user_workspace_root(current_username())


def summarize_source(item: dict) -> dict:
    """Reduce extracted-item payloads to metadata worth persisting and showing."""
    return {
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "source_type": item.get("source_type", ""),
        "extraction_method": item.get("extraction_method", ""),
    }


def process_input_sources(source_input: str, uploaded_files, result_count: int) -> tuple[list[dict], list]:
    """Collect extracted items and chunk them from search, URLs, and uploaded files."""
    manual_urls, google_query = extract_urls_and_queries(source_input)
    uploaded_files = uploaded_files or []

    if not google_query and not manual_urls and not uploaded_files:
        raise ValueError("Please provide a search topic, URL, YouTube link, TXT file, or PDF file.")

    extracted_items: list[dict] = []
    all_chunks = []

    if google_query:
        if not SERPER_API_KEY:
            raise ValueError("SERPER_API_KEY is required for search-based ingestion.")

        search_results = search_serper(google_query, int(result_count))
        for item in search_results:
            extracted_item = extract_content(
                url=item["link"],
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
            )
            if extracted_item.get("content"):
                extracted_items.append(extracted_item)

    for url in manual_urls:
        extracted_item = (
            create_extracted_item_from_youtube(url)
            if is_youtube_url(url)
            else extract_content(url=url, title=url, snippet="User provided URL")
        )
        if extracted_item.get("content"):
            extracted_items.append(extracted_item)

    for uploaded_file in uploaded_files:
        extracted_item = create_extracted_item_from_file(uploaded_file)
        if extracted_item.get("content"):
            extracted_items.append(extracted_item)

    for extracted_item in extracted_items:
        all_chunks.extend(process_extracted_content(extracted_item))

    return extracted_items, all_chunks


def build_workspace(workspace_name: str, source_input: str, uploaded_files, result_count: int) -> None:
    """Create a new persisted research workspace from mixed source inputs."""
    extracted_items, all_chunks = process_input_sources(source_input, uploaded_files, result_count)
    if not all_chunks:
        raise ValueError("No usable content was extracted from the provided sources.")

    workspace_title = workspace_name.strip() or f"Research Workspace {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    workspace_path = create_topic_folder(workspace_title, base_dir=current_workspace_root())
    vector_store = create_and_save_vector_store(all_chunks, save_path=workspace_path)

    save_metadata(
        workspace_path,
        {
            "topic": workspace_title,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_chunks": len(all_chunks),
            "total_sources": len(extracted_items),
            "embedding_model": EMBEDDING_MODEL_NAME,
            "sources": [summarize_source(item) for item in extracted_items],
        },
    )

    st.session_state["vector_store"] = vector_store
    st.session_state["vector_store_ready"] = True
    st.session_state["active_workspace_path"] = workspace_path
    st.session_state["active_workspace_name"] = workspace_title
    st.session_state["qa_history"] = []
    st.session_state["successful_documents"] = [summarize_source(item) for item in extracted_items]
    st.session_state["all_chunks"] = all_chunks
    reset_answer_state()


def load_saved_workspace(workspace_item: dict) -> None:
    """Restore a previously saved workspace into the current session."""
    st.session_state["active_workspace_path"] = workspace_item["folder_path"]
    st.session_state["active_workspace_name"] = workspace_item["topic"]
    st.session_state["vector_store"] = load_vector_store(workspace_item["folder_path"])
    st.session_state["vector_store_ready"] = True
    st.session_state["qa_history"] = load_chat_history(workspace_item["folder_path"])
    st.session_state["successful_documents"] = workspace_item.get("sources", [])
    st.session_state["all_chunks"] = []
    reset_answer_state()


def sign_out() -> None:
    """Clear authenticated session fields while preserving app defaults."""
    st.session_state["is_authenticated"] = False
    st.session_state["current_username"] = ""
    st.session_state["user_has_api_key"] = False
    st.session_state["user_groq_api_key"] = ""
    st.session_state["vector_store_ready"] = False
    st.session_state["vector_store"] = None
    st.session_state["active_workspace_path"] = ""
    st.session_state["active_workspace_name"] = ""
    st.session_state["qa_history"] = []
    st.session_state["successful_documents"] = []
    st.session_state["all_chunks"] = []
    reset_answer_state()


def render_auth_screen() -> None:
    """Render a simple local auth screen with sign-in and account creation."""
    st.title(APP_TITLE)
    st.caption("Sign in to build and manage your own research workspaces.")
    sign_in_tab, create_tab = st.tabs(["Sign In", "Create Account"])

    with sign_in_tab:
        with st.container(border=True):
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            if st.button("Sign In", use_container_width=True):
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
            new_username = st.text_input("Username", key="signup_username")
            new_password = st.text_input("Password", type="password", key="signup_password")
            if st.button("Create Account", use_container_width=True):
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
    """Require the signed-in user to save a Groq API key before entering the app."""
    st.title(APP_TITLE)
    st.caption("Connect Groq to enable grounded answer generation in your account.")

    with st.container(border=True):
        api_key_value = st.text_input("Groq API key", type="password")
        st.link_button("Get a Groq API key", "https://console.groq.com/keys", use_container_width=True)
        if st.button("Save API Key", use_container_width=True):
            if not api_key_value.strip():
                st.warning("Please enter a Groq API key.")
            else:
                save_user_groq_key(current_username(), api_key_value.strip())
                st.session_state["user_groq_api_key"] = api_key_value.strip()
                st.session_state["user_has_api_key"] = True
                st.rerun()


initialize_session_state()

if not st.session_state.get("is_authenticated"):
    render_auth_screen()
    st.stop()

if not st.session_state.get("user_has_api_key"):
    render_api_key_setup_screen()
    st.stop()

st.title(APP_TITLE)
st.caption("Research workspace builder for learning and experimenting with RAG.")

with st.sidebar:
    st.markdown("### Account")
    st.markdown(f"**{current_username()}**")
    if st.button("Sign Out", use_container_width=True):
        sign_out()
        st.rerun()

    usage = get_usage_summary(current_username())
    st.markdown("### Usage")
    st.metric("Total tokens", usage["total_tokens"])
    st.metric("Requests", usage["requests"])
    if usage.get("last_updated"):
        st.caption(f"Updated {usage['last_updated']}")

    st.markdown("### Workspace Storage")
    st.caption(f"User workspace root: `{current_workspace_root()}`")

    saved_workspaces = list_research_history(base_dir=current_workspace_root())
    if saved_workspaces:
        selected_workspace = st.selectbox(
            "Saved workspaces",
            options=saved_workspaces,
            format_func=lambda item: f"{item['topic']} | chunks: {item['total_chunks']}",
        )
        if st.button("Load Workspace", use_container_width=True):
            load_saved_workspace(selected_workspace)
            st.rerun()
    else:
        st.caption("No saved workspaces yet.")

build_tab, ask_tab, download_tab = st.tabs(["Build", "Ask", "Download"])

with build_tab:
    st.subheader("Build Research Workspace")
    st.caption("Combine search, URLs, YouTube transcripts, TXT files, and PDFs into one workspace.")

    with st.container(border=True):
        workspace_name = st.text_input(
            "Workspace name",
            value=st.session_state.get("active_workspace_name", ""),
            placeholder="Example: Multi-agent healthcare research",
        )
        source_input = st.text_area(
            "Search topic or paste URLs",
            placeholder=(
                "Example:\n"
                "latest multi-agent RAG systems\n\n"
                "https://example.com/article\n"
                "https://youtu.be/xxxx"
            ),
            height=180,
        )
        uploaded_files = st.file_uploader(
            "Upload TXT or PDF files",
            type=["txt", "pdf"],
            accept_multiple_files=True,
        )
        result_count = st.number_input(
            "Search results",
            min_value=1,
            max_value=20,
            value=DEFAULT_NUM_RESULTS,
            step=1,
        )

        if SERPER_API_KEY:
            st.success("SERPER_API_KEY detected. Search ingestion is enabled.")
        else:
            st.warning("Search ingestion is disabled until SERPER_API_KEY is configured.")

        if st.button("Build Workspace", use_container_width=True):
            with st.spinner("Building research workspace..."):
                try:
                    build_workspace(workspace_name, source_input, uploaded_files, int(result_count))
                except Exception as exc:
                    st.error(f"Workspace build failed: {exc}")
                else:
                    st.success("Research workspace created successfully.")

    if st.session_state.get("successful_documents"):
        st.subheader("Workspace Sources")
        for index, item in enumerate(st.session_state["successful_documents"], start=1):
            with st.container(border=True):
                st.markdown(f"**{index}. {item.get('title') or 'Untitled source'}**")
                st.caption(f"{item.get('source_type', 'source')} | {item.get('extraction_method', '')}")
                if item.get("url"):
                    st.write(item["url"])

with ask_tab:
    if not st.session_state.get("vector_store_ready"):
        st.info("Build or load a research workspace first to enable question answering.")
    else:
        st.subheader("Ask from Research Workspace")
        st.caption(f"Workspace: {st.session_state.get('active_workspace_name', 'Active workspace')}")
        with st.container(border=True):
            question = st.text_input(
                "Question",
                placeholder="Example: What are the main ideas across these sources?",
            )
            retrieval_k = st.number_input(
                "Chunks to retrieve",
                min_value=1,
                max_value=10,
                value=DEFAULT_RETRIEVAL_K,
                step=1,
            )
            st.caption(f"Groq answer model ready: {GROQ_MODEL}")

            if st.button("Generate Answer", use_container_width=True):
                try:
                    retrieved_chunks = retrieve_relevant_chunks(
                        vector_store=st.session_state["vector_store"],
                        question=question,
                        k=int(retrieval_k),
                    )
                    st.session_state["retrieved_chunks"] = retrieved_chunks
                    generation_result = generate_answer_with_usage(
                        question=question,
                        retrieved_chunks=retrieved_chunks,
                        api_key=st.session_state.get("user_groq_api_key"),
                    )
                    st.session_state["generated_answer"] = generation_result["answer"]
                    record_token_usage(current_username(), generation_result.get("usage", {}))
                    if st.session_state.get("active_workspace_path"):
                        st.session_state["qa_history"] = append_chat_message(
                            folder_path=st.session_state["active_workspace_path"],
                            question=question,
                            answer=st.session_state["generated_answer"],
                        )
                except Exception as exc:
                    st.error(f"Answer generation failed: {exc}")

        retrieved_chunks = st.session_state.get("retrieved_chunks", [])
        if retrieved_chunks:
            st.subheader("Retrieved Chunks")
            for index, item in enumerate(retrieved_chunks, start=1):
                with st.container(border=True):
                    st.markdown(f"**Chunk {index}**")
                    st.caption(item.get("title") or "Untitled source")
                    st.text_area(
                        f"Chunk preview {index}",
                        item["content"][:1800],
                        height=180,
                        key=f"retrieved_chunk_{index}",
                    )

        generated_answer = st.session_state.get("generated_answer", "")
        if generated_answer:
            st.subheader("Generated Answer")
            st.markdown(generated_answer)

with download_tab:
    qa_history = st.session_state.get("qa_history", [])
    if not qa_history:
        st.caption("No saved questions yet for the active workspace.")
    else:
        st.subheader("Export Conversation")
        export_scope = st.radio(
            "Export scope",
            ["Entire conversation", "Selected questions and answers"],
            horizontal=True,
        )
        export_theme = st.selectbox(
            "PDF theme",
            ["Light theme", "Dark theme"],
        )

        selected_history = qa_history
        if export_scope == "Selected questions and answers":
            options = [
                f"{item.get('time', 'Recent')} | {item.get('question', 'Untitled question')[:80]}"
                for item in qa_history
            ]
            selected_labels = st.multiselect(
                "Choose entries to export",
                options=options,
                default=options[:1] if options else [],
            )
            selected_history = [
                item for item, label in zip(qa_history, options) if label in selected_labels
            ]
            if not selected_history:
                st.warning("Please select at least one question and answer to export.")
                selected_history = []

        if selected_history:
            selected_theme = "light" if export_theme == "Light theme" else "dark"
            file_suffix = "light" if selected_theme == "light" else "dark"
            pdf_bytes = build_chat_history_pdf(
                selected_history,
                workspace_name=st.session_state.get("active_workspace_name", "research_workspace"),
                theme=selected_theme,
            )
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=f"{slugify_filename(st.session_state.get('active_workspace_name', 'research_workspace'))}_chat_{file_suffix}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        st.subheader("Conversation History")
        for index, item in enumerate(reversed(qa_history), start=1):
            with st.container(border=True):
                st.markdown(f"**Q{index}. {item.get('question', '')}**")
                st.caption(item.get("time", ""))
                st.markdown(item.get("answer", ""))
