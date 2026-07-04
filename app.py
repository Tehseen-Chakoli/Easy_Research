"""Early application shell for Easy Research."""

import streamlit as st

from src.config import APP_TITLE, DEFAULT_NUM_RESULTS, SERPER_API_KEY


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

    if SERPER_API_KEY:
        st.success("SERPER_API_KEY detected. Search integration can be wired next.")
    else:
        st.warning("SERPER_API_KEY is not configured yet. Add it to the environment before enabling search.")

    st.write("Current query preview:", research_query or "No topic entered yet")
    st.write("Configured result count:", int(result_count))

st.info("Next step: connect search ingestion and content extraction to the research setup flow.")
