"""Early application shell for Easy Research."""

from datetime import datetime

import streamlit as st

from src.answer_generator import generate_answer_from_chunks
from src.chat_history_manager import append_chat_message, load_chat_history
from src.config import (
    APP_TITLE,
    BASE_VECTOR_DIR,
    DEFAULT_NUM_RESULTS,
    DEFAULT_RETRIEVAL_K,
    EMBEDDING_MODEL_NAME,
    GROQ_API_KEY,
    GROQ_MODEL,
    SERPER_API_KEY,
)
from src.document_processor import process_extracted_content
from src.history_manager import create_topic_folder, list_research_history, save_metadata
from src.retriever import retrieve_relevant_chunks
from src.serper_search import search_serper
from src.vector_store import create_and_save_vector_store, load_vector_store
from src.web_extractor import extract_content


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="ER",
    layout="wide",
)

# Seed the minimal session state needed for the early ingestion flow.
if "search_results" not in st.session_state:
    st.session_state["search_results"] = []
if "extracted_item" not in st.session_state:
    st.session_state["extracted_item"] = None
if "chunked_documents" not in st.session_state:
    st.session_state["chunked_documents"] = []
if "vector_store_ready" not in st.session_state:
    st.session_state["vector_store_ready"] = False
if "vector_store" not in st.session_state:
    st.session_state["vector_store"] = None
if "retrieved_chunks" not in st.session_state:
    st.session_state["retrieved_chunks"] = []
if "generated_answer" not in st.session_state:
    st.session_state["generated_answer"] = ""
if "active_workspace_path" not in st.session_state:
    st.session_state["active_workspace_path"] = ""
if "active_workspace_name" not in st.session_state:
    st.session_state["active_workspace_name"] = ""
if "qa_history" not in st.session_state:
    st.session_state["qa_history"] = []

st.title(APP_TITLE)
st.caption("Research workspace builder for learning and experimenting with RAG.")

st.markdown(
    """
    Easy Research is a practical project for building a research-oriented
    Retrieval-Augmented Generation workflow.

    The application foundation now includes:
    - a structured `src/` package
    - environment-driven configuration
    - an initial research input flow
    - a Streamlit interface ready for ingestion features
    """
)

    with st.container(border=True):
        workspace_name = st.text_input(
            "Workspace name",
            value=st.session_state.get("active_workspace_name", ""),
            placeholder="Example: Multi-agent healthcare research",
        )
        st.subheader("Research setup")
        research_query = st.text_input(
            "Research topic",
            placeholder="Example: latest multi-agent RAG systems",
        )
    result_count = st.number_input(
        "Planned search results",
        min_value=1,
        max_value=20,
        value=DEFAULT_NUM_RESULTS,
        step=1,
    )
    search_clicked = st.button("Search Research Sources", use_container_width=True)

    if SERPER_API_KEY:
        st.success("SERPER_API_KEY detected. Search integration is ready.")
    else:
        st.warning("SERPER_API_KEY is not configured yet. Add it to the environment before enabling search.")

    st.write("Current query preview:", research_query or "No topic entered yet")
    st.write("Configured result count:", int(result_count))
    if workspace_name.strip():
        st.write("Active workspace name:", workspace_name)

saved_workspaces = list_research_history()
if saved_workspaces:
    with st.sidebar:
        st.markdown("### Saved Workspaces")
        selected_workspace = st.selectbox(
            "Open saved workspace",
            options=saved_workspaces,
            format_func=lambda item: f"{item['topic']} | chunks: {item['total_chunks']}",
        )
        if st.button("Load Workspace", use_container_width=True):
            st.session_state["active_workspace_path"] = selected_workspace["folder_path"]
            st.session_state["active_workspace_name"] = selected_workspace["topic"]
            st.session_state["vector_store"] = load_vector_store(selected_workspace["folder_path"])
            st.session_state["vector_store_ready"] = True
            st.session_state["qa_history"] = load_chat_history(selected_workspace["folder_path"])
            st.session_state["search_results"] = []
            st.session_state["extracted_item"] = None
            st.session_state["chunked_documents"] = []
            st.session_state["retrieved_chunks"] = []
            st.session_state["generated_answer"] = ""
            st.rerun()

if search_clicked:
    if not research_query.strip():
        st.warning("Please enter a research topic before searching.")
    elif not SERPER_API_KEY:
        st.error("Search is unavailable because SERPER_API_KEY is missing.")
    else:
        with st.spinner("Searching research sources..."):
            try:
                search_results = search_serper(research_query, int(result_count))
            except Exception as exc:
                st.error(f"Search failed: {exc}")
            else:
                st.session_state["search_results"] = search_results
                st.session_state["extracted_item"] = None
                if not search_results:
                    st.info("No organic results were returned for this query.")

search_results = st.session_state.get("search_results", [])

if search_results:
    st.subheader("Search Results")
    for index, item in enumerate(search_results, start=1):
        with st.container(border=True):
            st.markdown(f"**{index}. {item['title'] or 'Untitled result'}**")
            st.caption(item["link"])
            if item["snippet"]:
                st.write(item["snippet"])

            if st.button("Extract Content", key=f"extract_result_{index}", use_container_width=True):
                with st.spinner("Extracting readable page content..."):
                    try:
                        st.session_state["extracted_item"] = extract_content(
                            url=item["link"],
                            title=item.get("title", ""),
                            snippet=item.get("snippet", ""),
                        )
                        st.session_state["chunked_documents"] = []
                        st.session_state["vector_store_ready"] = False
                        st.session_state["vector_store"] = None
                        st.session_state["retrieved_chunks"] = []
                        st.session_state["generated_answer"] = ""
                    except Exception as exc:
                        st.session_state["extracted_item"] = {
                            "title": item.get("title", ""),
                            "url": item["link"],
                            "snippet": item.get("snippet", ""),
                            "content": None,
                            "extraction_method": None,
                            "error": str(exc),
                        }

extracted_item = st.session_state.get("extracted_item")
if extracted_item:
    st.subheader("Extracted Content Preview")
    if extracted_item.get("content"):
        st.success(f"Content extracted using {extracted_item.get('extraction_method')}.")
        st.text_area(
            "Preview",
            extracted_item["content"][:4000],
            height=320,
        )

        # Chunking is the first RAG-specific processing step after extraction.
        if st.button("Create Document Chunks", use_container_width=True):
            chunked_documents = process_extracted_content(extracted_item)
            st.session_state["chunked_documents"] = chunked_documents
            st.session_state["vector_store_ready"] = False
            st.session_state["vector_store"] = None
            st.session_state["retrieved_chunks"] = []
            st.session_state["generated_answer"] = ""
    else:
        error_text = extracted_item.get("error") or "No readable content could be extracted."
        st.error(error_text)

chunked_documents = st.session_state.get("chunked_documents", [])
if chunked_documents:
    st.subheader("Chunk Preview")
    st.success(f"Created {len(chunked_documents)} chunks from the extracted content.")

    first_chunk = chunked_documents[0]
    st.caption(
        f"Chunk metadata: title={first_chunk.metadata.get('title', '')} | "
        f"method={first_chunk.metadata.get('extraction_method', '')}"
    )
    st.text_area(
        "First chunk",
        first_chunk.page_content[:2500],
        height=260,
    )

    # Once chunking is available, the next milestone is turning chunks into vectors.
    if st.button("Create Vector Store", use_container_width=True):
        with st.spinner("Building vector store from chunked documents..."):
            workspace_title = workspace_name.strip() or f"Research Workspace {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            workspace_path = create_topic_folder(workspace_title)
            st.session_state["vector_store"] = create_and_save_vector_store(
                chunked_documents,
                save_path=workspace_path,
            )
            st.session_state["active_workspace_path"] = workspace_path
            st.session_state["active_workspace_name"] = workspace_title
            st.session_state["vector_store_ready"] = True
            st.session_state["retrieved_chunks"] = []
            st.session_state["generated_answer"] = ""
            st.session_state["qa_history"] = []

            source_url = extracted_item.get("url", "") if extracted_item else ""
            save_metadata(
                workspace_path,
                {
                    "topic": workspace_title,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_chunks": len(chunked_documents),
                    "source_url": source_url,
                    "embedding_model": EMBEDDING_MODEL_NAME,
                },
            )

vector_store_ready = st.session_state.get("vector_store_ready", False)
if vector_store_ready:
    st.subheader("Vector Store Status")
    st.success("Vector store created successfully.")
    st.caption(f"Embedding model: {EMBEDDING_MODEL_NAME}")
    if st.session_state.get("active_workspace_name"):
        st.caption(f"Workspace: {st.session_state['active_workspace_name']}")

    with st.container(border=True):
        st.subheader("Ask from Research Store")
        question = st.text_input(
            "Question",
            placeholder="Example: What are the main ideas in this source?",
        )
        retrieval_k = st.number_input(
            "Chunks to retrieve",
            min_value=1,
            max_value=10,
            value=DEFAULT_RETRIEVAL_K,
            step=1,
        )
        retrieve_clicked = st.button("Retrieve Relevant Chunks", use_container_width=True)

        if GROQ_API_KEY:
            st.caption(f"Groq answer model ready: {GROQ_MODEL}")
        else:
            st.caption("Add GROQ_API_KEY to enable grounded answer generation.")

        if retrieve_clicked:
            try:
                st.session_state["retrieved_chunks"] = retrieve_relevant_chunks(
                    vector_store=st.session_state["vector_store"],
                    question=question,
                    k=int(retrieval_k),
                )
                st.session_state["generated_answer"] = ""
            except Exception as exc:
                st.error(f"Retrieval failed: {exc}")

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

    if st.button("Generate Grounded Answer", use_container_width=True):
        try:
            st.session_state["generated_answer"] = generate_answer_from_chunks(
                question=question,
                retrieved_chunks=retrieved_chunks,
            )
            if st.session_state.get("active_workspace_path"):
                st.session_state["qa_history"] = append_chat_message(
                    folder_path=st.session_state["active_workspace_path"],
                    question=question,
                    answer=st.session_state["generated_answer"],
                )
        except Exception as exc:
            st.error(f"Answer generation failed: {exc}")

generated_answer = st.session_state.get("generated_answer", "")
if generated_answer:
    st.subheader("Generated Answer")
    st.markdown(generated_answer)

qa_history = st.session_state.get("qa_history", [])
if qa_history:
    st.subheader("Chat History")
    for index, item in enumerate(reversed(qa_history), start=1):
        with st.container(border=True):
            st.markdown(f"**Q{index}. {item.get('question', '')}**")
            st.caption(item.get("time", ""))
            st.markdown(item.get("answer", ""))

st.info("Next step: expand the app with additional ingestion sources, better UI organization, and export features.")
