from __future__ import annotations

from slack_kb.models import AnswerResult


def format_answer(result: AnswerResult) -> str:
    if result.refused:
        return result.answer
    source_lines = []
    for index, hit in enumerate(result.hits, start=1):
        label = f"[{index}] {hit.title}"
        source_lines.append(f"<{hit.source_url}|{label}>" if hit.source_url else label)
    return f"{result.answer}\n\n*Sources*\n" + "\n".join(source_lines)


HELP_TEXT = """*Intelligent Knowledge Base*
• `/knowledge ask <question>`
• `/knowledge add personal <URL or text>`
• `/knowledge add team <URL or text>` (channel only)
• `/knowledge add org <URL or text>`
• `/knowledge summarize <document-id>`
• `/knowledge status`

You can also mention me with the same command. Attach a PDF, DOCX, TXT, or Markdown
file and write `add personal`, `add team`, or `add org`."""
