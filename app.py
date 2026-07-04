"""Early application shell for Easy Research."""

import streamlit as st

from src.config import APP_TITLE, DEFAULT_NUM_RESULTS, EMBEDDING_MODEL_NAME, SERPER_API_KEY
from src.document_processor import process_extracted_content
from src.serper_search import search_serper
from src.vector_store import create_vector_store
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
            st.session_state["vector_store"] = create_vector_store(chunked_documents)
            st.session_state["vector_store_ready"] = True

vector_store_ready = st.session_state.get("vector_store_ready", False)
if vector_store_ready:
    st.subheader("Vector Store Status")
    st.success("Vector store created successfully.")
    st.caption(f"Embedding model: {EMBEDDING_MODEL_NAME}")

st.info("Next step: store chunked research documents for retrieval and question answering.")
