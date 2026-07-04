"""Uploaded file normalization for the research workspace builder."""

from __future__ import annotations

from src.pdf_loader import create_extracted_item_from_pdf


def read_txt_file(uploaded_file) -> str:
    """Read the contents of an uploaded text file with tolerant decoding."""
    try:
        text = uploaded_file.read().decode("utf-8", errors="ignore")
        return text.strip()
    except Exception as exc:
        raise RuntimeError(f"Failed to read TXT file: {exc}") from exc


def create_extracted_item_from_txt(uploaded_file) -> dict:
    """Normalize an uploaded TXT file into the extracted-item schema."""
    content = read_txt_file(uploaded_file)
    if not content:
        raise ValueError("Uploaded TXT file is empty.")

    return {
        "title": uploaded_file.name,
        "url": uploaded_file.name,
        "snippet": "Uploaded TXT file",
        "content": content,
        "extraction_method": "txt_upload",
        "source_type": "txt_file",
    }


def create_extracted_item_from_file(uploaded_file) -> dict:
    """Route supported uploaded files to the correct ingestion handler."""
    file_name = uploaded_file.name.lower()
    if file_name.endswith(".txt"):
        return create_extracted_item_from_txt(uploaded_file)
    if file_name.endswith(".pdf"):
        return create_extracted_item_from_pdf(uploaded_file)

    raise ValueError(
        f"Unsupported file type: {uploaded_file.name}. Supported types: .txt, .pdf"
    )
