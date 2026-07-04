"""
Easy Answer - Multi-Source RAG Research Assistant
Consolidated app with best features from all versions.
"""

import asyncio
import html
import uuid
from datetime import datetime

import streamlit as st

from src.config import SERPER_API_KEY
from src.serper_search import search_serper
from src.web_extractor import extract_content
from src.conversation_memory import save_generated_answer

from src.history_manager import (
    create_topic_folder,
    save_metadata,
    delete_research_database,
)

from src.vector_store import (
    create_and_save_vector_store,
    load_vector_store,
)

from src.retriever import retrieve_relevant_chunks
from src.answer_generator import generate_answer_with_usage

from src.file_ingestor import create_extracted_item_from_file
from src.youtube_loader import create_extracted_item_from_youtube
from src.pdf_loader import create_extracted_item_from_pdf

from src.session_state import (
    initialize_session_state,
    widget_key,
    reset_loaded_data,
    reset_input_fields_only,
)

from src.input_parser import (
    is_youtube_url,
    extract_urls_and_queries,
)

from src.chat_history_manager import (
    append_chat_message,
)

from src.user_manager import (
    record_token_usage,
)
from src.ui_components import (
    render_api_key_setup_screen,
    render_auth_screen,
    render_chat_export_controls,
    render_chat_history_list,
    render_page_hero,
    render_usage_panel,
)
from src.ui_styles import APP_STYLES
from src.workspace_manager import (
    get_current_workspace_root,
    get_sorted_history,
    process_extracted_item_into_chunks,
    restore_workspace_session,
)


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Easy Answer - Multi Source RAG",
    page_icon="EA",
    layout="wide",
)

initialize_session_state()
st.markdown(APP_STYLES, unsafe_allow_html=True)


def get_current_username() -> str | None:
    """Return the active signed-in username from session state."""
    return st.session_state.get("current_username")


# =====================================================
# AUTH GATE
# =====================================================

if not st.session_state.get("is_authenticated"):
    render_auth_screen()
    st.stop()

if not st.session_state.get("user_has_api_key"):
    render_api_key_setup_screen()
    st.stop()


# =====================================================
# DATABASE STARTUP SCREEN
# =====================================================

history = get_sorted_history()
render_page_hero()

if not st.session_state["db_mode_selected"]:
    with st.container(border=True):
        db_choice = st.radio(
            "Start here",
            ["Create new workspace", "Open saved workspace"],
            horizontal=True,
            key=widget_key("db_choice"),
        )

        if db_choice == "Create new workspace":
            new_db_name = st.text_input(
                "Workspace name",
                value="Research Workspace",
                key=widget_key("new_db_name"),
            )

            if st.button("Create workspace", use_container_width=True, key=widget_key("create_db_btn")):
                if not new_db_name.strip():
                    st.warning("Please enter a workspace name.")
                    st.stop()

                dataset_id = str(uuid.uuid4())[:8]
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                final_db_name = f"{new_db_name.strip()} | {current_time}"

                st.session_state["db_mode_selected"] = True
                st.session_state["active_db_name"] = final_db_name
                st.session_state["query"] = final_db_name
                st.session_state["dataset_id"] = dataset_id
                st.session_state["active_topic_folder"] = None
                st.session_state["qa_history"] = []
                st.session_state["created_at"] = current_time

                st.rerun()

        else:
            if not history:
                st.info("No saved workspaces found. Create one to get started.")
                st.stop()

            selected_existing_db = st.selectbox(
                "Saved workspaces",
                options=history,
                format_func=lambda x: f"{x.get('topic', '')} | Sources: {x.get('total_sources', 0)} | Chunks: {x.get('total_chunks', 0)}",
                key=widget_key("startup_existing_db"),
            )

            if st.button("Open workspace", use_container_width=True, key=widget_key("use_existing_db_btn")):
                with st.spinner("Loading selected research workspace..."):
                    vector_store = load_vector_store(selected_existing_db["folder_path"])

                restore_workspace_session(selected_existing_db, vector_store)

                st.rerun()

    st.stop()


# =====================================================
# SIDEBAR - WORKSPACE & HISTORY
# =====================================================

st.sidebar.markdown("### Account")
st.sidebar.markdown(f"**{html.escape(get_current_username() or 'User')}**")
if st.sidebar.button("Sign Out", key=widget_key("sign_out_btn"), use_container_width=True):
    reset_loaded_data()
    st.session_state["is_authenticated"] = False
    st.session_state["current_username"] = None
    st.session_state["user_has_api_key"] = False
    st.session_state["user_groq_api_key"] = ""
    st.rerun()

render_usage_panel()

st.sidebar.markdown("### Research Workspace")

if st.session_state.get("active_db_name"):
    st.sidebar.markdown(f"**{html.escape(st.session_state['active_db_name'])}**")
    st.sidebar.caption("Active research workspace")
else:
    st.sidebar.caption("No research workspace active yet.")

history = get_sorted_history()

if history:
    st.sidebar.markdown("### Research Workspaces")
    selected_history = st.sidebar.selectbox(
        "Open workspace",
        options=history,
        format_func=lambda x: f"{x.get('topic', '')} | Sources: {x.get('total_sources', 0)}",
        key=widget_key("selected_history_dropdown"),
    )

    if st.sidebar.button("Open", key=widget_key("switch_db_btn"), use_container_width=True):
        with st.spinner("Switching research workspace..."):
            vector_store = load_vector_store(selected_history["folder_path"])

        restore_workspace_session(selected_history, vector_store)
        st.rerun()
else:
    st.sidebar.caption("No saved workspaces yet.")

with st.sidebar.expander("More actions", expanded=False):
    if st.session_state.get("delete_success_message"):
        st.success(st.session_state.pop("delete_success_message"))

    if history:
        db_to_delete = st.selectbox(
            "Delete workspace",
            options=history,
            format_func=lambda x: f"{x.get('topic', '')} | Sources: {x.get('total_sources', 0)}",
            key=widget_key("delete_db_select"),
        )

        confirm_delete = st.checkbox(
            "Confirm deletion",
            key=widget_key("confirm_delete_db"),
        )

        if st.button("Delete workspace", key=widget_key("delete_db_btn"), use_container_width=True):
            if not confirm_delete:
                st.warning("Please confirm before deleting.")
            else:
                try:
                    deleted_db_name = db_to_delete.get("topic", "Database")
                    delete_research_database(
                        db_to_delete["folder_path"],
                        base_dir=get_current_workspace_root(),
                    )

                    if st.session_state.get("active_topic_folder") == db_to_delete["folder_path"]:
                        current_username = get_current_username()
                        current_api_key = st.session_state.get("user_groq_api_key", "")
                        reset_loaded_data()
                        st.session_state["is_authenticated"] = True
                        st.session_state["current_username"] = current_username
                        st.session_state["user_has_api_key"] = bool(current_api_key)
                        st.session_state["user_groq_api_key"] = current_api_key
                        st.session_state["db_mode_selected"] = False
                        st.session_state["active_db_name"] = None
                        st.session_state.pop("vector_store", None)

                    st.session_state["delete_success_message"] = f"Deleted research workspace: {deleted_db_name}"
                    st.rerun()

                except Exception as e:
                    st.error(f"Delete failed: {e}")

    if st.button("Reset Workspace", key=widget_key("clear_current_session_btn"), use_container_width=True):
        current_username = get_current_username()
        current_api_key = st.session_state.get("user_groq_api_key", "")
        reset_loaded_data()
        st.session_state["is_authenticated"] = True
        st.session_state["current_username"] = current_username
        st.session_state["user_has_api_key"] = bool(current_api_key)
        st.session_state["user_groq_api_key"] = current_api_key
        st.rerun()


# =====================================================
# WORKSPACE TABS
# =====================================================

st.markdown('<div class="section-label">Research Workspace</div>', unsafe_allow_html=True)
build_tab, ask_tab, history_tab = st.tabs(["Build", "Ask", "Download"])

with build_tab:
    st.markdown('<div class="panel-heading">Build a research workspace</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-subheading">Combine search results, URLs, PDFs, and TXT files into one focused research set.</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        research_name = st.text_input(
            "Research workspace name",
            value=st.session_state.get("query", "Research Workspace"),
            disabled=True,
            key=widget_key("research_name"),
        )

        source_input = st.text_area(
            "Search query or paste URLs",
            placeholder=(
                "Try something like:\n"
                "latest AI agents in healthcare\n\n"
                "https://example.com/article\n"
                "https://youtube.com/watch?v=xxxx\n\n"
                "You can mix search text and links in one box."
            ),
            height=180,
            key=widget_key("source_input"),
        )

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            uploaded_files = st.file_uploader(
                "Upload TXT or PDF",
                type=["txt", "pdf"],
                accept_multiple_files=True,
                key=widget_key("file_uploader"),
            )

        with col2:
            google_num_results = st.number_input(
                "Search results",
                min_value=1,
                max_value=50,
                value=5,
                step=1,
                key=widget_key("google_num_results"),
            )

        with col3:
            st.write("")
            st.write("")
            load_clicked = st.button("Build workspace", use_container_width=True, key=widget_key("load_data_btn"))

    if not SERPER_API_KEY:
        st.warning("Google search is disabled because SERPER_API_KEY is missing. URLs and files can still be loaded.")

    if st.session_state.get("load_success_message"):
        st.success(st.session_state.pop("load_success_message"))


# =====================================================
# LOAD DATA PIPELINE
# =====================================================

if load_clicked:
    manual_urls, google_topic = extract_urls_and_queries(source_input)
    uploaded_files = uploaded_files or []

    has_google_topic = bool(google_topic.strip())
    has_urls = bool(manual_urls)
    has_files = bool(uploaded_files)

    if not has_google_topic and not has_urls and not has_files:
        st.warning("Please provide at least one source: search text, URL, YouTube URL, TXT, or PDF.")
        st.stop()

    dataset_id = st.session_state.get("dataset_id") or str(uuid.uuid4())[:8]
    st.session_state["dataset_id"] = dataset_id

    final_db_name = st.session_state.get("active_db_name")
    if not final_db_name:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_db_name = f"{research_name.strip()} | {current_time}"
        st.session_state["active_db_name"] = final_db_name
        st.session_state["query"] = final_db_name
        st.session_state["created_at"] = current_time

    new_chunks = []
    new_successful_documents = []

    total_items = 1
    if has_google_topic:
        total_items += int(google_num_results)
    total_items += len(manual_urls)
    total_items += len(uploaded_files)

    completed_items = 0
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(message, completed):
        completed += 1
        progress = min(completed / max(total_items, 1), 1.0)
        status_text.info(message)
        progress_bar.progress(progress)
        return completed

    # =====================================================
    # GOOGLE SEARCH EXTRACTION
    # =====================================================
    if has_google_topic:
        if not SERPER_API_KEY:
            st.error("SERPER_API_KEY is missing. Google search cannot run.")
            st.stop()

        try:
            status_text.info("Searching Google...")
            search_results = search_serper(google_topic.strip(), int(google_num_results))

            for idx, result in enumerate(search_results, start=1):
                try:
                    status_text.info(f"Extracting Google page {idx}...")

                    extracted_item = asyncio.run(
                        extract_content(
                            url=result["link"],
                            title=result.get("title", f"Google Result {idx}"),
                            snippet=result.get("snippet", ""),
                        )
                    )

                    if extracted_item.get("content"):
                        chunks, processed_item = process_extracted_item_into_chunks(
                            extracted_item=extracted_item,
                            source_type="google_search",
                            dataset_id=dataset_id,
                        )
                        new_chunks.extend(chunks)
                        new_successful_documents.append(processed_item)

                    completed_items = update_progress(f"Google page {idx} processed.", completed_items)

                except Exception as e:
                    completed_items = update_progress(f"Skipped Google page {idx}: {type(e).__name__}", completed_items)

        except Exception as e:
            st.error(f"Google search failed: {e}")
            st.stop()

    # =====================================================
    # MANUAL URL / YOUTUBE
    # =====================================================
    for idx, url in enumerate(manual_urls, start=1):
        try:
            if is_youtube_url(url):
                status_text.info(f"Processing YouTube URL {idx}...")
                extracted_item = create_extracted_item_from_youtube(url)

                chunks, processed_item = process_extracted_item_into_chunks(
                    extracted_item=extracted_item,
                    source_type="youtube_url",
                    dataset_id=dataset_id,
                )

            else:
                status_text.info(f"Processing website URL {idx}...")
                extracted_item = asyncio.run(
                    extract_content(
                        url=url,
                        title=f"User Provided URL {idx}",
                        snippet="User provided URL",
                    )
                )

                if not extracted_item.get("content"):
                    completed_items = update_progress(f"Skipped URL {idx}. No extractable content found.", completed_items)
                    continue

                chunks, processed_item = process_extracted_item_into_chunks(
                    extracted_item=extracted_item,
                    source_type="manual_url",
                    dataset_id=dataset_id,
                )

            new_chunks.extend(chunks)
            new_successful_documents.append(processed_item)
            completed_items = update_progress(f"URL {idx} processed.", completed_items)

        except Exception as e:
            completed_items = update_progress(f"Skipped URL {idx}: {type(e).__name__}", completed_items)

    # =====================================================
    # FILE EXTRACTION
    # =====================================================
    for idx, uploaded_file in enumerate(uploaded_files, start=1):
        try:
            file_name = uploaded_file.name.lower()

            if file_name.endswith(".txt"):
                status_text.info(f"Processing TXT file {idx}...")
                extracted_item = create_extracted_item_from_file(uploaded_file)

                chunks, processed_item = process_extracted_item_into_chunks(
                    extracted_item=extracted_item,
                    source_type="txt_file",
                    dataset_id=dataset_id,
                )

            elif file_name.endswith(".pdf"):
                status_text.info(f"Processing PDF file {idx}...")
                extracted_item = create_extracted_item_from_pdf(uploaded_file)

                chunks, processed_item = process_extracted_item_into_chunks(
                    extracted_item=extracted_item,
                    source_type="pdf_file",
                    dataset_id=dataset_id,
                )

            else:
                completed_items = update_progress(f"Skipped unsupported file {idx}.", completed_items)
                continue

            new_chunks.extend(chunks)
            new_successful_documents.append(processed_item)
            completed_items = update_progress(f"File {idx} processed.", completed_items)

        except Exception as e:
            completed_items = update_progress(f"Skipped file {idx}: {type(e).__name__}", completed_items)

    if not new_chunks:
        progress_bar.empty()
        status_text.empty()
        st.error("No usable content was extracted.")
        st.stop()

    # =====================================================
    # CREATE OR UPDATE VECTOR DB
    # =====================================================
    status_text.info("Creating or updating research workspace...")

    existing_vector_store = st.session_state.get("vector_store")
    existing_chunks = st.session_state.get("all_chunks", [])
    existing_chunk_count = st.session_state.get("existing_chunk_count", len(existing_chunks))
    existing_documents = st.session_state.get("successful_documents", [])
    topic_folder = st.session_state.get("active_topic_folder")

    if topic_folder:
        try:
            if existing_vector_store is not None:
                existing_vector_store.add_documents(new_chunks)
                existing_vector_store.save_local(topic_folder)
                vector_store = existing_vector_store
            else:
                all_chunks_for_store = existing_chunks + new_chunks
                vector_store = create_and_save_vector_store(chunks=all_chunks_for_store, save_path=topic_folder)
        except Exception:
            if not existing_chunks:
                raise
            all_chunks_for_store = existing_chunks + new_chunks
            vector_store = create_and_save_vector_store(chunks=all_chunks_for_store, save_path=topic_folder)
    else:
        topic_folder = create_topic_folder(final_db_name, base_dir=get_current_workspace_root())
        st.session_state["active_topic_folder"] = topic_folder
        vector_store = create_and_save_vector_store(chunks=new_chunks, save_path=topic_folder)

    all_chunks = existing_chunks + new_chunks
    all_successful_documents = existing_documents + new_successful_documents
    total_chunk_count = int(existing_chunk_count) + len(new_chunks)
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ensure created_at is set for new databases
    if "created_at" not in st.session_state:
        st.session_state["created_at"] = now_text

    metadata = {
        "topic": final_db_name,
        "dataset_id": dataset_id,
        "created_at": st.session_state.get("created_at", now_text),
        "updated_at": now_text,
        "total_chunks": total_chunk_count,
        "total_sources": len(all_successful_documents),
        "embedding_model": "BAAI/bge-base-en-v1.5",
        "vector_store_type": "FAISS",
        "storage_path": topic_folder,
        "sources": [
            {
                "source_id": doc.get("source_id"),
                "source_type": doc.get("source_type"),
                "title": doc.get("title"),
                "url": doc.get("url"),
                "extraction_method": doc.get("extraction_method"),
            }
            for doc in all_successful_documents
        ],
    }

    save_metadata(topic_folder, metadata)

    st.session_state["all_chunks"] = all_chunks
    st.session_state["existing_chunk_count"] = total_chunk_count
    st.session_state["successful_documents"] = all_successful_documents
    st.session_state["query"] = final_db_name
    st.session_state["dataset_id"] = dataset_id
    st.session_state["vector_store"] = vector_store
    st.session_state["active_topic_folder"] = topic_folder
    st.session_state["active_db_name"] = final_db_name

    progress_bar.progress(1.0)
    status_text.success("Research workspace updated successfully.")

    st.session_state["load_success_message"] = (
        f"Research workspace ready. New sources added: {len(new_successful_documents)}. "
        f"Total sources in the current workspace: {len(all_successful_documents)}."
    )

    reset_input_fields_only()
    st.rerun()


with ask_tab:
    st.markdown('<div class="panel-heading">Ask a question</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-subheading">Use the active research workspace to generate grounded answers with citations.</div>',
        unsafe_allow_html=True,
    )

    if "vector_store" in st.session_state:
        with st.container(border=True):
            answer_question = st.text_input(
                "Question",
                placeholder="Ask anything from the active research workspace...",
                key=widget_key("answer_question"),
            )

            col_a, col_b = st.columns([1, 1])

            with col_a:
                answer_top_k = st.number_input(
                    "Chunks to review",
                    min_value=1,
                    max_value=50,
                    value=5,
                    step=1,
                    key=widget_key("answer_top_k"),
                )

            with col_b:
                st.write("")
                st.write("")
                ask_clicked = st.button("Generate Answer", use_container_width=True, key=widget_key("generate_answer_btn"))

        if ask_clicked:
            if not answer_question.strip():
                st.warning("Please enter a question.")
                st.stop()

            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.info("Retrieving relevant information...")
            progress_bar.progress(40)

            retrieved_chunks = retrieve_relevant_chunks(
                vector_store=st.session_state["vector_store"],
                question=answer_question,
                k=int(answer_top_k),
            )

            status_text.info("Generating answer...")
            progress_bar.progress(80)

            try:
                generation_result = generate_answer_with_usage(
                    question=answer_question,
                    retrieved_chunks=retrieved_chunks,
                    api_key=st.session_state.get("user_groq_api_key"),
                )
            except Exception as e:
                progress_bar.empty()
                status_text.error("Answer generation failed.")
                st.error(str(e))
                st.stop()

            final_answer = generation_result["answer"]
            record_token_usage(
                get_current_username(),
                generation_result.get("usage", {}),
            )
            save_generated_answer(answer_question, final_answer)
            progress_bar.progress(100)
            status_text.success("Answer generated.")

            st.session_state["qa_history"] = append_chat_message(
                folder_path=st.session_state.get("active_topic_folder"),
                question=answer_question,
                answer=final_answer,
            )

            st.rerun()
    else:
        st.info("Load or switch to a research workspace first to enable question answering.")

    st.markdown("#### Recent Questions")
    render_chat_history_list()

with history_tab:
    st.markdown('<div class="panel-heading">Download conversation</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-subheading">Choose a theme and export either the full conversation or selected questions and answers.</div>',
        unsafe_allow_html=True,
    )
    render_chat_export_controls()
