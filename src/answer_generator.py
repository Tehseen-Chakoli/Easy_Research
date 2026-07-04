"""Groq-backed answer generation and citation formatting for RAG responses."""

import os
import re

from groq import Groq
from dotenv import load_dotenv

from src.conversation_memory import get_recent_answers_context

load_dotenv()


def build_context_from_chunks(retrieved_chunks):
    """Serialize retrieved chunks into a citation-numbered prompt context."""
    context_parts = []

    for i, item in enumerate(retrieved_chunks, start=1):
        source_text = f"""
Citation Number: [{i}]

Title:
{item.get("title", "")}

URL:
{item.get("url", "")}

Content:
{item.get("content", "")}
"""
        context_parts.append(source_text)

    return "\n\n".join(context_parts)


def build_rag_prompt(question, retrieved_chunks):
    """Build the final answer-generation prompt with context and memory."""
    context = build_context_from_chunks(retrieved_chunks)
    recent_context = get_recent_answers_context()

    prompt = f"""
You are an advanced AI research assistant.

Answer the user question ONLY from the provided retrieved context.

Rules:
1. Answer ONLY from the retrieved context.
2. Do not hallucinate or invent facts.
3. Use citation numbers inside the answer like [1], [2], [3].
4. Do NOT paste full URLs inside the main answer.
5. Keep the answer clean, structured, and readable.
6. If the answer includes code, format it in fenced Markdown code blocks with the correct language when obvious.
7. Preserve indentation inside code examples.
8. If the retrieved context does not support a code example, say that clearly instead of inventing one.

Required answer format:

## Answer

Write the answer here using citations like [1], [2].

Conversation Memory:
{recent_context}

User Question:
{question}


Retrieved Context:
{context}


Final Answer:
"""

    return prompt


def _strip_existing_sources_section(answer_text: str) -> str:
    """Remove any model-generated sources section before rebuilding citations."""
    pattern = re.compile(r"\n##\s*Sources\s*$.*", re.IGNORECASE | re.DOTALL)
    return re.sub(pattern, "", (answer_text or "").strip()).strip()


def _extract_citation_numbers(answer_text: str, max_index: int) -> list[int]:
    """Collect unique citation markers that reference valid retrieved chunks."""
    numbers = []
    seen = set()

    for match in re.findall(r"\[(\d+)\]", answer_text or ""):
        value = int(match)
        if 1 <= value <= max_index and value not in seen:
            seen.add(value)
            numbers.append(value)

    return numbers


def _build_sources_section(retrieved_chunks: list, citation_numbers: list[int]) -> str:
    """Build a de-duplicated sources appendix from the cited chunks only."""
    source_lines = []
    seen_urls = set()

    for citation_number in citation_numbers:
        item = retrieved_chunks[citation_number - 1]
        title = (item.get("title") or "Untitled source").strip()
        url = (item.get("url") or "").strip()

        if url and url in seen_urls:
            continue

        if url:
            seen_urls.add(url)
            source_lines.append(f"[{citation_number}] {title} - {url}")
        else:
            source_lines.append(f"[{citation_number}] {title}")

    if not source_lines:
        return ""

    return "## Sources\n\n" + "\n".join(source_lines)


def format_grounded_answer(answer_text: str, retrieved_chunks: list) -> str:
    """Normalize the model answer and append a clean sources section."""
    cleaned_answer = _strip_existing_sources_section(answer_text)
    citation_numbers = _extract_citation_numbers(cleaned_answer, len(retrieved_chunks))
    sources_section = _build_sources_section(retrieved_chunks, citation_numbers)

    if sources_section:
        return f"{cleaned_answer}\n\n{sources_section}".strip()

    return cleaned_answer


def generate_with_groq(prompt, model_name=None, api_key=None):
    """Call the Groq chat completion API and return answer plus token usage."""
    api_key = api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No Groq API key is configured for this account.")

    model_name = model_name or os.getenv(
        "GROQ_MODEL",
        "llama-3.1-8b-instant"
    )

    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a grounded research assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )
    except Exception as exc:
        error_text = str(exc)
        status_code = getattr(exc, "status_code", None)

        if status_code == 401 or "invalid_api_key" in error_text.lower():
            raise RuntimeError(
                "Groq rejected the API key. Please update the saved Groq API key for this account."
            ) from exc

        raise RuntimeError(f"Groq request failed: {error_text}") from exc

    usage = getattr(response, "usage", None)
    usage_payload = {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
        "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
        "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
    }

    return {
        "answer": response.choices[0].message.content,
        "usage": usage_payload,
    }


def generate_answer_from_chunks(question, retrieved_chunks, model_name=None, api_key=None):
    """Generate a formatted grounded answer from retrieved chunks."""
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if not retrieved_chunks:
        raise ValueError("No retrieved chunks found.")

    prompt = build_rag_prompt(
        question=question,
        retrieved_chunks=retrieved_chunks
    )

    result = generate_with_groq(
        prompt=prompt,
        model_name=model_name,
        api_key=api_key,
    )
    return format_grounded_answer(result["answer"], retrieved_chunks)


def generate_answer_with_usage(question, retrieved_chunks, model_name=None, api_key=None):
    """Generate a grounded answer and preserve usage details for the UI."""
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if not retrieved_chunks:
        raise ValueError("No retrieved chunks found.")

    prompt = build_rag_prompt(
        question=question,
        retrieved_chunks=retrieved_chunks
    )

    result = generate_with_groq(
        prompt=prompt,
        model_name=model_name,
        api_key=api_key,
    )
    result["answer"] = format_grounded_answer(result["answer"], retrieved_chunks)
    return result
