"""Grounded answer generation for retrieved research chunks."""

from __future__ import annotations

from groq import Groq

from src.config import GROQ_API_KEY, GROQ_MODEL


def build_context_from_chunks(retrieved_chunks: list[dict]) -> str:
    """Serialize retrieved chunks into a citation-numbered prompt context."""
    context_parts = []
    for index, item in enumerate(retrieved_chunks, start=1):
        context_parts.append(
            f"""
Citation Number: [{index}]

Title:
{item.get("title", "")}

URL:
{item.get("url", "")}

Content:
{item.get("content", "")}
""".strip()
        )
    return "\n\n".join(context_parts)


def build_rag_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    """Build the first grounded-answer prompt for the Groq chat model."""
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


def generate_with_groq(prompt: str, api_key: str | None = None, model_name: str | None = None) -> str:
    """Call the Groq API for the current answer-generation step."""
    resolved_api_key = (api_key or GROQ_API_KEY or "").strip()
    if not resolved_api_key:
        raise ValueError("GROQ_API_KEY is missing.")

    client = Groq(api_key=resolved_api_key)
    response = client.chat.completions.create(
        model=model_name or GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You answer from retrieved research context."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def generate_with_groq_and_usage(
    prompt: str,
    api_key: str | None = None,
    model_name: str | None = None,
) -> dict:
    """Call Groq and return both the answer text and token-usage payload."""
    resolved_api_key = (api_key or GROQ_API_KEY or "").strip()
    if not resolved_api_key:
        raise ValueError("GROQ_API_KEY is missing.")

    client = Groq(api_key=resolved_api_key)
    response = client.chat.completions.create(
        model=model_name or GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You answer from retrieved research context."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    usage = getattr(response, "usage", None)
    return {
        "answer": response.choices[0].message.content or "",
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
            "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
        },
    }


def generate_answer_from_chunks(question: str, retrieved_chunks: list[dict]) -> str:
    """Generate a grounded answer from the retrieved chunk set."""
    if not retrieved_chunks:
        raise ValueError("No retrieved chunks found.")

    prompt = build_rag_prompt(question, retrieved_chunks)
    return generate_with_groq(prompt)


def generate_answer_with_usage(
    question: str,
    retrieved_chunks: list[dict],
    api_key: str | None = None,
) -> dict:
    """Generate an answer and return the associated token-usage details."""
    if not retrieved_chunks:
        raise ValueError("No retrieved chunks found.")

    prompt = build_rag_prompt(question, retrieved_chunks)
    return generate_with_groq_and_usage(prompt, api_key=api_key)
