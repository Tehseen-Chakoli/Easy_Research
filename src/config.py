"""Environment-backed configuration for Easy Research."""

from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


APP_TITLE = "Easy Research"
DEFAULT_NUM_RESULTS = int(os.getenv("DEFAULT_NUM_RESULTS", "5"))
SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
