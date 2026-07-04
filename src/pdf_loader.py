"""PDF ingestion helpers for uploaded research documents."""

from __future__ import annotations

import os
import tempfile

import fitz


def save_uploaded_pdf_temporarily(uploaded_file) -> str:
    """Write an uploaded PDF to a temporary file for extraction."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        return temp_file.name


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract selectable text from a PDF using PyMuPDF."""
    text_parts = []
    document = fitz.open(pdf_path)

    try:
        for page_number, page in enumerate(document, start=1):
            page_text = page.get_text("text")
            if page_text and page_text.strip():
                text_parts.append(f"\n--- Page {page_number} ---\n{page_text}")
    finally:
        document.close()

    return "\n".join(text_parts).strip()


def create_extracted_item_from_pdf(uploaded_file) -> dict:
    """Normalize PDF file content into the shared extracted-item schema."""
    pdf_path = save_uploaded_pdf_temporarily(uploaded_file)

    try:
        extracted_text = extract_text_from_pdf(pdf_path)
        if not extracted_text:
            raise ValueError("No readable text found in PDF.")

        return {
            "title": uploaded_file.name,
            "url": uploaded_file.name,
            "snippet": "PDF uploaded document content",
            "content": extracted_text,
            "extraction_method": "pymupdf_text_extraction",
            "source_type": "pdf_file",
            "file_name": uploaded_file.name,
        }
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
