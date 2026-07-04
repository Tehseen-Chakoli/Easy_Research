from __future__ import annotations

import re
import textwrap
from datetime import datetime
from typing import Iterable

import fitz


PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT_MARGIN = 48
RIGHT_MARGIN = 48
TOP_MARGIN = 52
BOTTOM_MARGIN = 52
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
TITLE_FONT = "Times-Bold"
BODY_FONT = "Times-Roman"
BODY_BOLD_FONT = "Times-Bold"
CODE_FONT = "Courier"


def slugify_filename(value: str) -> str:
    value = (value or "chat_export").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value or "chat_export"


def _theme_colors(theme: str):
    normalized = (theme or "light").strip().lower()

    if normalized == "dark":
        return {
            "background": (0.07, 0.07, 0.07),
            "text": (0.97, 0.97, 0.97),
            "muted": (0.82, 0.82, 0.82),
            "accent": (0.58, 0.82, 1.0),
            "border": (0.27, 0.27, 0.27),
        }

    return {
        "background": (1, 1, 1),
        "text": (0.1, 0.1, 0.1),
        "muted": (0.38, 0.38, 0.38),
        "accent": (0.11, 0.39, 0.24),
        "border": (0.8, 0.8, 0.8),
    }


def _wrap_text(text: str, width: int = 86) -> list[str]:
    lines: list[str] = []
    for paragraph in (text or "").splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(paragraph.strip(), width=width, break_long_words=False))
    return lines or [""]


def _ensure_page(doc, theme_colors):
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    page.draw_rect(
        fitz.Rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT),
        fill=theme_colors["background"],
        color=theme_colors["background"],
    )
    return page


def _draw_header(page, title: str, workspace_name: str, generated_at: str, theme_colors):
    page.insert_text(
        (LEFT_MARGIN, TOP_MARGIN),
        title,
        fontname=TITLE_FONT,
        fontsize=20,
        color=theme_colors["text"],
    )
    page.insert_text(
        (LEFT_MARGIN, TOP_MARGIN + 24),
        f"Research Workspace: {workspace_name}",
        fontname=BODY_FONT,
        fontsize=11,
        color=theme_colors["muted"],
    )
    page.insert_text(
        (LEFT_MARGIN, TOP_MARGIN + 40),
        f"Generated: {generated_at}",
        fontname=BODY_FONT,
        fontsize=10,
        color=theme_colors["muted"],
    )
    page.draw_line(
        (LEFT_MARGIN, TOP_MARGIN + 54),
        (PAGE_WIDTH - RIGHT_MARGIN, TOP_MARGIN + 54),
        color=theme_colors["border"],
        width=0.8,
    )


def _draw_wrapped_lines(
    page,
    lines: Iterable[str],
    y: float,
    theme_colors,
    fontname: str,
    fontsize: float,
    line_height: float,
):
    for line in lines:
        page.insert_text(
            (LEFT_MARGIN, y),
            line,
            fontname=fontname,
            fontsize=fontsize,
            color=theme_colors["text"],
        )
        y += line_height
    return y


def _split_markdown_sections(text: str) -> list[dict]:
    sections = []
    parts = re.split(r"```(\w+)?\n(.*?)```", text or "", flags=re.DOTALL)

    if not parts:
        return [{"type": "text", "content": text or ""}]

    sections.append({"type": "text", "content": parts[0]})
    index = 1
    while index + 1 < len(parts):
        language = (parts[index] or "text").strip()
        code = parts[index + 1].rstrip()
        sections.append({
            "type": "code",
            "language": language,
            "content": code,
        })
        trailing = parts[index + 2] if index + 2 < len(parts) else ""
        sections.append({"type": "text", "content": trailing})
        index += 3

    return [section for section in sections if section.get("content")]


def _code_colors(theme: str):
    if (theme or "").lower() == "dark":
        return {
            "background": (0.10, 0.13, 0.20),
            "border": (0.24, 0.31, 0.44),
            "default": (0.92, 0.95, 0.98),
            "keyword": (0.58, 0.74, 0.98),
            "string": (0.61, 0.85, 0.59),
            "comment": (0.62, 0.71, 0.62),
            "number": (0.98, 0.78, 0.44),
        }

    return {
        "background": (0.94, 0.96, 0.99),
        "border": (0.78, 0.84, 0.91),
        "default": (0.15, 0.20, 0.27),
        "keyword": (0.18, 0.36, 0.78),
        "string": (0.10, 0.47, 0.18),
        "comment": (0.42, 0.49, 0.42),
        "number": (0.67, 0.41, 0.03),
    }


def _token_spans(line: str):
    token_pattern = re.compile(
        r"(#.*$|\"[^\"]*\"|'[^']*'|\b(?:def|class|return|import|from|for|while|if|elif|else|try|except|with|as|print|yield|lambda|in|not|and|or|True|False|None)\b|\b\d+(?:\.\d+)?\b)"
    )

    spans = []
    last_index = 0
    for match in token_pattern.finditer(line):
        start, end = match.span()
        if start > last_index:
            spans.append(("default", line[last_index:start]))

        token = match.group(0)
        if token.startswith("#"):
            spans.append(("comment", token))
        elif token.startswith('"') or token.startswith("'"):
            spans.append(("string", token))
        elif re.fullmatch(r"\d+(?:\.\d+)?", token):
            spans.append(("number", token))
        else:
            spans.append(("keyword", token))

        last_index = end

    if last_index < len(line):
        spans.append(("default", line[last_index:]))

    return spans or [("default", line)]


def _wrap_code_lines(code_text: str, max_chars: int) -> list[str]:
    wrapped_lines: list[str] = []

    for raw_line in (code_text or "").splitlines() or [""]:
        if raw_line == "":
            wrapped_lines.append("")
            continue

        remaining = raw_line
        while len(remaining) > max_chars:
            split_at = remaining.rfind(" ", 0, max_chars + 1)
            if split_at <= 0:
                split_at = max_chars

            wrapped_lines.append(remaining[:split_at])
            remaining = remaining[split_at:]

            if remaining.startswith(" "):
                remaining = remaining[1:]

        wrapped_lines.append(remaining)

    return wrapped_lines or [""]


def _draw_code_block(page, code_text: str, y: float, theme: str):
    colors = _code_colors(theme)
    char_width = 6.1
    max_chars = max(int((CONTENT_WIDTH - 24) / char_width), 24)
    lines = _wrap_code_lines(code_text, max_chars)
    line_height = 14
    block_height = 20 + (len(lines) * line_height)
    block_rect = fitz.Rect(LEFT_MARGIN, y, PAGE_WIDTH - RIGHT_MARGIN, y + block_height)

    page.draw_rect(
        block_rect,
        fill=colors["background"],
        color=colors["border"],
    )

    current_y = y + 16

    for line in lines:
        current_x = LEFT_MARGIN + 12
        for token_type, token_text in _token_spans(line):
            page.insert_text(
                (current_x, current_y),
                token_text,
                fontname=CODE_FONT,
                fontsize=10.5,
                color=colors[token_type],
            )
            current_x += len(token_text) * char_width
        current_y += line_height

    return y + block_height + 10


def build_chat_history_pdf(chat_history: list[dict], workspace_name: str, theme: str = "light") -> bytes:
    theme_colors = _theme_colors(theme)
    content_start_y = TOP_MARGIN + 78
    export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    doc = fitz.open()
    page = _ensure_page(doc, theme_colors)
    _draw_header(
        page=page,
        title="Easy Answer Chat Export",
        workspace_name=workspace_name or "Untitled",
        generated_at=export_time,
        theme_colors=theme_colors,
    )

    y = content_start_y

    if not chat_history:
        page.insert_text(
            (LEFT_MARGIN, y),
            "No conversation history was available for export.",
            fontname=BODY_FONT,
            fontsize=12,
            color=theme_colors["text"],
        )
        return doc.tobytes()

    for index, message in enumerate(chat_history, start=1):
        question = message.get("question", "").strip()
        answer = message.get("answer", "").strip()
        time_text = message.get("time", "").strip()

        question_lines = _wrap_text(question, width=76)
        answer_sections = _split_markdown_sections(answer)
        block_title = f"Conversation {index}"
        answer_line_count = 0
        for section in answer_sections:
            if section["type"] == "code":
                wrapped_code_lines = _wrap_code_lines(section["content"], max(int((CONTENT_WIDTH - 24) / 6.1), 24))
                answer_line_count += len(wrapped_code_lines) + 2
            else:
                answer_line_count += len(_wrap_text(section["content"], width=76))

        block_lines = 2 + len(question_lines) + answer_line_count
        estimated_height = 92 + (block_lines * 16)
        if y > content_start_y and y + estimated_height > PAGE_HEIGHT - BOTTOM_MARGIN:
            page = _ensure_page(doc, theme_colors)
            _draw_header(
                page=page,
                title="Easy Answer Chat Export",
                workspace_name=workspace_name or "Untitled",
                generated_at=export_time,
                theme_colors=theme_colors,
            )
            y = content_start_y

        page.insert_text(
            (LEFT_MARGIN, y),
            block_title,
            fontname=BODY_BOLD_FONT,
            fontsize=13,
            color=theme_colors["accent"],
        )
        y += 18

        if time_text:
            page.insert_text(
                (LEFT_MARGIN, y),
                time_text,
                fontname=BODY_FONT,
                fontsize=10,
                color=theme_colors["muted"],
            )
            y += 14

        page.insert_text(
            (LEFT_MARGIN, y),
            "Question",
            fontname=BODY_BOLD_FONT,
            fontsize=11,
            color=theme_colors["text"],
        )
        y += 14
        y = _draw_wrapped_lines(
            page=page,
            lines=question_lines,
            y=y,
            theme_colors=theme_colors,
            fontname=BODY_FONT,
            fontsize=11,
            line_height=14,
        )
        y += 6

        page.insert_text(
            (LEFT_MARGIN, y),
            "Answer",
            fontname=BODY_BOLD_FONT,
            fontsize=11,
            color=theme_colors["text"],
        )
        y += 14

        for section in answer_sections:
            if section["type"] == "code":
                code_lines = _wrap_code_lines(section["content"], max(int((CONTENT_WIDTH - 24) / 6.1), 24))
                required_height = 30 + (len(code_lines) * 14)
                if y > content_start_y and y + required_height > PAGE_HEIGHT - BOTTOM_MARGIN:
                    page = _ensure_page(doc, theme_colors)
                    _draw_header(
                        page=page,
                        title="Easy Answer Chat Export",
                        workspace_name=workspace_name or "Untitled",
                        generated_at=export_time,
                        theme_colors=theme_colors,
                    )
                    y = content_start_y
                y = _draw_code_block(page, section["content"], y, theme)
            else:
                answer_lines = _wrap_text(section["content"], width=76)
                if answer_lines:
                    y = _draw_wrapped_lines(
                        page=page,
                        lines=answer_lines,
                        y=y,
                        theme_colors=theme_colors,
                        fontname=BODY_FONT,
                        fontsize=11,
                        line_height=14,
                    )
                    y += 6
        y += 18

    return doc.tobytes()
