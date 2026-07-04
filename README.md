# Easy Research

<p align="center">
  <img src="https://img.shields.io/badge/status-under%20development-F59E0B?style=for-the-badge" alt="Under Development" />
  <img src="https://img.shields.io/badge/Streamlit-app-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/project-learning%20rag-2563EB?style=for-the-badge" alt="Learning RAG" />
</p>

Easy Research is a personal learning project focused on building a research-oriented RAG application step by step. The goal is to turn search-driven research inputs into a structured local workflow for retrieval and grounded answering.

## Current Status

The project now has:

- a Streamlit application shell
- a base `src/` package
- environment-backed configuration
- a starter research setup interface
- working Serper search integration
- displayed organic search results in the UI
- readable web content extraction
- extracted page preview inside the UI
- document creation and chunking
- chunk preview for extracted research content
- a clean local development baseline

## Project Direction

The goal is to evolve this into a multi-source research workspace that can:

- collect information from search results, URLs, documents, and transcripts
- build a local retrieval pipeline
- generate grounded answers from stored research material
- support a practical end-to-end research workflow

## Run Locally

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Environment Setup

Create a local `.env` file from the provided example:

```env
SERPER_API_KEY=your_serper_api_key
GROQ_MODEL=llama-3.1-8b-instant
```

At this stage:

- `SERPER_API_KEY` powers the current research search flow
- `GROQ_MODEL` is reserved for the answer-generation layer that will be added later

## Current Focus

The current codebase has started source discovery and is now ready to expand into:

- retrieval and vector storage
- grounded answer generation

## Implemented So Far

The application can now:

- accept a research topic in the Streamlit UI
- call the Serper API using environment-based configuration
- display normalized organic search results for the current query
- extract readable page content from a selected result
- preview normalized extracted content before document processing
- convert extracted content into LangChain documents
- split extracted content into retrieval-ready chunks

## RAG Processing Step

After extraction, the current pipeline now:

1. creates a LangChain `Document`
2. preserves source metadata on that document
3. splits the content into overlapping chunks
4. previews the first chunk in the UI

## Extraction Pipeline

The current web ingestion path works in two stages:

1. try `trafilatura` for readable article-style extraction
2. fall back to `requests` + `BeautifulSoup` for HTML text parsing
