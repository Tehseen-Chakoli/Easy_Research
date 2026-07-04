"""Early application shell for Easy Research."""

import streamlit as st

from src.config import APP_TITLE, DEFAULT_NUM_RESULTS, SERPER_API_KEY
from src.serper_search import search_serper


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="ER",
    layout="wide",
)

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
                if not search_results:
                    st.info("No organic results were returned for this query.")
                else:
                    st.subheader("Search Results")
                    for index, item in enumerate(search_results, start=1):
                        with st.container(border=True):
                            st.markdown(f"**{index}. {item['title'] or 'Untitled result'}**")
                            st.caption(item["link"])
                            if item["snippet"]:
                                st.write(item["snippet"])

st.info("Next step: connect web extraction and document processing to these search results.")
