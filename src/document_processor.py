"""Document creation and chunking helpers for extracted research content."""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE


def create_document(extracted_item: dict) -> Document | None:
    """Convert extracted content into a LangChain document with source metadata."""
    content = extracted_item.get("content")
    if not content:
        return None

    return Document(
        page_content=content,
        metadata={
            "title": extracted_item.get("title"),
            "url": extracted_item.get("url"),
            "snippet": extracted_item.get("snippet"),
            "extraction_method": extracted_item.get("extraction_method"),
        },
    )


def chunk_document(
    document: Document,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Document]:
    """Split a research document into overlapping chunks for later retrieval."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return text_splitter.split_documents([document])


def process_extracted_content(extracted_item: dict) -> list[Document]:
    """Create and chunk a document, returning an empty list for blank content."""
    document = create_document(extracted_item)
    if not document:
        return []
    return chunk_document(document)
