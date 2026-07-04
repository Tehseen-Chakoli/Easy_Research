"""Helpers for normalizing uploaded files into extracted-item payloads."""

from typing import Dict, Any

from src.pdf_loader import create_extracted_item_from_pdf


def read_txt_file(uploaded_file) -> str:
    """Read the contents of an uploaded text file using tolerant UTF-8 decoding."""
    try:
        text = uploaded_file.read().decode("utf-8", errors="ignore")
        return text.strip()
    except Exception as exc:
        raise RuntimeError(f"Failed to read TXT file: {exc}") from exc


def create_extracted_item_from_txt(uploaded_file) -> Dict[str, Any]:
    """Normalize an uploaded TXT file into the common extracted-item schema."""
    content = read_txt_file(uploaded_file)

    if not content:
        raise ValueError("Uploaded TXT file is empty.")

    extracted_item = {
        "title": uploaded_file.name,
        "url": uploaded_file.name,
        "snippet": "Uploaded TXT file",
        "content": content,
        "extraction_method": "txt_upload",
        "source_type": "txt_file",
    }

    return extracted_item


def create_extracted_item_from_file(uploaded_file) -> Dict[str, Any]:
    """Route an uploaded file to the correct ingestion handler by extension."""
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):
        return create_extracted_item_from_txt(uploaded_file)

    if file_name.endswith(".pdf"):
        return create_extracted_item_from_pdf(uploaded_file)

    raise ValueError(
        f"Unsupported file type: {uploaded_file.name}. "
        f"Supported types: .txt, .pdf"
    )
