"""Batch 1 bootstrap app for Easy Research."""

import streamlit as st


st.set_page_config(
    page_title="Easy Research",
    page_icon="ER",
    layout="wide",
)

st.title("Easy Research")
st.caption("Under development: starting the RAG workspace builder from scratch.")

st.markdown(
    """
    Easy Research is being built as a practical learning project around
    Retrieval-Augmented Generation (RAG).

    This first batch sets up the project foundation:
    - Streamlit application shell
    - dependency manifest
    - Git hygiene
    - development README
    """
)

with st.container(border=True):
    st.subheader("Current milestone")
    st.write("Project bootstrap and initial UI shell")
    st.info("Upcoming batches will add config, ingestion, retrieval, and answer generation.")
