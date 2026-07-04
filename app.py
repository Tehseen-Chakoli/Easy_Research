"""Early application shell for Easy Research."""

import streamlit as st

from src.config import APP_TITLE, DEFAULT_NUM_RESULTS, SERPER_API_KEY
from src.serper_search import search_serper
from src.web_extractor import extract_content


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="ER",
    layout="wide",
)

if "search_results" not in st.session_state:
    st.session_state["search_results"] = []

if "extracted_item" not in st.session_state:
    st.session_state["extracted_item"] = None

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
    else:
        error_text = extracted_item.get("error") or "No readable content could be extracted."
        st.error(error_text)

st.info("Next step: turn extracted content into chunked research documents for retrieval.")
