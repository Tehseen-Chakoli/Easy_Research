# Easy Research

<p align="center">
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Groq-LLM-F55036?style=for-the-badge" alt="Groq" />
  <img src="https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=for-the-badge" alt="LangChain" />
  <img src="https://img.shields.io/badge/FAISS-Vector%20Store-2563EB?style=for-the-badge" alt="FAISS" />
  <img src="https://img.shields.io/badge/PyMuPDF-PDF%20Export-7C3AED?style=for-the-badge" alt="PyMuPDF" />
  <img src="https://img.shields.io/badge/BeautifulSoup-Web%20Parsing-2E8B57?style=for-the-badge" alt="BeautifulSoup" />
</p>

Easy Research is a local-first RAG learning project built to turn scattered research inputs into a usable workspace. A user can create a personal account, save a Groq API key, build research workspaces from search results, URLs, YouTube transcripts, TXT files, and PDFs, then ask grounded questions against the stored knowledge base and export conversations as themed PDF reports.

## What the App Does

- creates user-scoped research workspaces
- supports search, web, YouTube, TXT, and PDF ingestion
- chunks and embeds source content locally
- stores vector indexes with FAISS
- retrieves relevant chunks for each question
- generates grounded answers with Groq
- tracks token usage per user
- saves workspace chat history
- exports selected or full conversations to light or dark themed PDFs

## Product Screens

### Build Workspace

![Build workspace view](docs/images/Home_Page.png)

### Ask Questions

![Ask view](docs/images/Ask.png)

### Download Exports

![Download view](docs/images/Download.png)

## End-to-End Flow

```text
User Login
   |
   +--> Save Groq API Key
   |
   +--> Create Research Workspace
           |
           +--> Search / URL / YouTube / TXT / PDF
                    |
                    v
             Extraction + Normalization
                    |
                    v
              LangChain Documents
                    |
                    v
               Text Chunking
                    |
                    v
         Hugging Face Embeddings + FAISS
                    |
                    v
              Retrieval for Question
                    |
                    v
             Groq Grounded Answer
                    |
                    v
       Chat History + Themed PDF Export
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| UI | Streamlit |
| Authentication | Local JSON-backed user storage |
| Search | Serper API |
| Web extraction | `trafilatura`, `requests`, `BeautifulSoup` |
| YouTube transcripts | `youtube-transcript-api` |
| Chunking | LangChain text splitters |
| Embeddings | Hugging Face sentence-transformers |
| Vector store | FAISS |
| Answer generation | Groq |
| PDF parsing/export | PyMuPDF |

## Repository Layout

```text
Easy_Research/
|-- app.py
|-- .env.example
|-- requirements.txt
|-- README.md
|-- docs/
|   `-- images/
|       |-- Home_Page.png
|       |-- Ask.png
|       `-- Download.png
`-- src/
    |-- answer_generator.py
    |-- chat_export.py
    |-- chat_history_manager.py
    |-- config.py
    |-- document_processor.py
    |-- file_ingestor.py
    |-- history_manager.py
    |-- input_parser.py
    |-- pdf_loader.py
    |-- retriever.py
    |-- serper_search.py
    |-- user_manager.py
    |-- vector_store.py
    |-- web_extractor.py
    `-- youtube_loader.py
```

## Key Implementation Highlights

### 1. Mixed-source workspace building

This is the part that lets one workspace combine search results, direct URLs, YouTube links, and uploaded files.

```python
def process_input_sources(source_input: str, uploaded_files, result_count: int) -> tuple[list[dict], list]:
    manual_urls, google_query = extract_urls_and_queries(source_input)
    uploaded_files = uploaded_files or []

    if not google_query and not manual_urls and not uploaded_files:
        raise ValueError("Please provide a search topic, URL, YouTube link, TXT file, or PDF file.")

    extracted_items: list[dict] = []
    all_chunks = []

    if google_query:
        search_results = search_serper(google_query, int(result_count))
        for item in search_results:
            extracted_item = extract_content(
                url=item["link"],
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
            )
            if extracted_item.get("content"):
                extracted_items.append(extracted_item)
```

### 2. Local vector-store creation

The vector pipeline uses sentence-transformer embeddings with FAISS persistence.

```python
def create_and_save_vector_store(chunks, save_path: str) -> FAISS:
    vector_store = create_vector_store(chunks)
    os.makedirs(save_path, exist_ok=True)
    vector_store.save_local(save_path)
    return vector_store


def load_vector_store(save_path: str) -> FAISS:
    return FAISS.load_local(
        folder_path=save_path,
        embeddings=get_embedding_model(),
        allow_dangerous_deserialization=True,
    )
```

### 3. Grounded answer generation with citations

The answer prompt is built directly from retrieved chunks and passed to Groq with a citation-oriented structure.

```python
def build_rag_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    context = build_context_from_chunks(retrieved_chunks)
    return f"""
You are a grounded research assistant.

Answer the user question using only the provided retrieved context.

Rules:
1. Do not invent facts.
2. Use citation markers like [1], [2], [3].
3. Keep the answer clean and readable.
4. If the context is insufficient, say so clearly.

User Question:
{question}

Retrieved Context:
{context}

Final Answer:
""".strip()
```

### 4. Themed PDF export

Conversation exports support light and dark themes, and code blocks are rendered with a dedicated monospaced layout.

```python
def build_chat_history_pdf(chat_history: list[dict], workspace_name: str, theme: str = "light") -> bytes:
    theme_colors = _theme_colors(theme)
    content_start_y = TOP_MARGIN + 78
    export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    doc = fitz.open()
    page = _ensure_page(doc, theme_colors)
    _draw_header(
        page=page,
        title="Easy Research Chat Export",
        workspace_name=workspace_name or "Untitled",
        generated_at=export_time,
        theme_colors=theme_colors,
    )
```

## Features in the Current Build

- local sign-up and sign-in flow
- per-user saved Groq API keys
- per-user token usage tracking
- research workspace creation and reload
- persistent FAISS indexes
- persistent Q&A history
- newest-first history display inside the ask flow
- download tab dedicated to export actions
- light and dark PDF theme selection
- selected-entry or full-conversation PDF downloads

## Local Setup

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create `.env`

Use the provided `.env.example` as reference:

```env
SERPER_API_KEY=your_serper_api_key
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
```

Notes:

- `SERPER_API_KEY` is needed for search-result ingestion
- `GROQ_MODEL` sets the default model name
- the app can store a user-specific Groq API key after login

## Run the App

```powershell
streamlit run app.py
```

Default local URL:

```text
http://localhost:8501
```

## Storage Model

### User data

The app stores local account data and usage metadata under internal auth storage.

### Research workspaces

Each user gets a dedicated workspace root. Every saved research workspace can contain:

- FAISS index files
- workspace metadata
- saved source summaries
- chat history for exports and reload

## Why This Project Matters

This project is useful as a learning build because it covers the full practical RAG path rather than only isolated experiments:

- data ingestion
- extraction cleanup
- chunking
- embedding
- vector retrieval
- grounded answer generation
- persistence
- user isolation
- export-ready output

## Current Status

The repository is in a solid usable state for local development and portfolio demonstration. The core workflow is complete: authenticate, build a workspace, ask grounded questions, review saved history, and export polished PDFs.

## License

No open-source license is included right now.

For a personal learning and portfolio project, that is completely fine. Without a license, others can view the code on GitHub, but they do not automatically have permission to reuse, modify, or redistribute it.
