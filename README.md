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
- embedding model configuration
- in-memory FAISS vector store creation
- similarity-based chunk retrieval
- first grounded answer-generation flow with Groq
- saved workspace metadata
- persisted FAISS workspace storage
- chat history persistence and reload
- mixed source ingestion from search, URLs, YouTube, TXT, and PDF
- tabbed workspace flow for build, ask, and history
- local authentication and sign-in flow
- per-user workspace isolation
- saved Groq API key and token usage tracking
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
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
```

At this stage:

- `SERPER_API_KEY` powers the current research search flow
- `GROQ_API_KEY` enables grounded answer generation
- `GROQ_MODEL` configures the active answer model

## Current Focus

The current codebase now supports the first complete RAG loop and is ready to expand into:

- export and interface polish
- richer UI refinement

## Implemented So Far

The application can now:

- accept a research topic in the Streamlit UI
- call the Serper API using environment-based configuration
- display normalized organic search results for the current query
- extract readable page content from a selected result
- preview normalized extracted content before document processing
- convert extracted content into LangChain documents
- split extracted content into retrieval-ready chunks
- create embeddings for processed chunks
- build an initial FAISS vector store from those chunks
- retrieve the most relevant chunks for a question
- generate a grounded answer from retrieved context using Groq
- save research workspaces locally
- reload saved workspaces later
- persist chat history per workspace
- combine multiple source types into one research workspace
- sign in with a local user account
- save a Groq API key per user
- track token usage by account

## RAG Processing Step

After extraction, the current pipeline now:

1. creates a LangChain `Document`
2. preserves source metadata on that document
3. splits the content into overlapping chunks
4. previews the first chunk in the UI
5. creates an in-memory vector store from the chunk set

## Vectorization Step

The application now includes the first vector indexing layer:

1. use a Hugging Face embedding model
2. normalize embeddings for retrieval-oriented similarity search
3. build a FAISS index from the processed research chunks

## Retrieval and Answering

The current question-answering flow now works like this:

1. create a vector store from the processed chunk set
2. retrieve the top matching chunks for the current question
3. build a grounded prompt from those retrieved chunks
4. send the prompt to Groq for answer generation
5. render the final answer in the Streamlit UI

## Persistence Layer

The application now persists core research state to disk:

1. save FAISS indexes into timestamped workspace folders
2. store workspace metadata as JSON
3. append Q&A history to workspace-level chat files
4. reload a saved workspace and continue asking questions later

## Account Layer

The application now includes a local account system:

1. users can create accounts and sign in
2. each user gets a dedicated workspace root
3. each user can save a private Groq API key
4. token usage is accumulated per account

## Multi-Source Ingestion

The build flow now supports combining multiple source types in one workspace:

1. search query text for Serper-powered source discovery
2. pasted website URLs
3. pasted YouTube links with transcript extraction
4. uploaded TXT files
5. uploaded PDF files

## Extraction Pipeline

The current web ingestion path works in two stages:

1. try `trafilatura` for readable article-style extraction
2. fall back to `requests` + `BeautifulSoup` for HTML text parsing
