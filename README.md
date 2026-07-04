# Easy Research

<p align="center">
  <img src="https://img.shields.io/badge/status-under%20development-F59E0B?style=for-the-badge" alt="Under Development" />
  <img src="https://img.shields.io/badge/Streamlit-app-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/project-learning%20rag-2563EB?style=for-the-badge" alt="Learning RAG" />
</p>

Easy Research is a personal learning project focused on building a research-oriented RAG application step by step. The Git history for this repository is being created in batches so each push reflects a meaningful milestone in the build process.

## Current Status

This repository is in its first setup batch.

Included in this batch:

- initial Streamlit app shell
- dependency manifest
- base `.gitignore`
- starter README

## Project Direction

The goal is to evolve this into a multi-source research workspace that can:

- collect information from search results, URLs, documents, and transcripts
- build a local retrieval pipeline
- generate grounded answers from stored research material
- grow incrementally with visible development history

## Run Locally

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Planned Next Batch

The next batch is expected to add:

- environment configuration
- project structure under `src/`
- initial setup for search/config handling
