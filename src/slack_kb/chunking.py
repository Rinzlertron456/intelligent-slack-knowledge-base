from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, *, max_chars: int = 3500, overlap_chars: int = 350) -> list[str]:
    clean = normalize_text(text)
    if not clean:
        return []

    paragraphs = [part.strip() for part in clean.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            start = 0
            while start < len(paragraph):
                end = min(start + max_chars, len(paragraph))
                chunks.append(paragraph[start:end].strip())
                if end == len(paragraph):
                    break
                start = max(end - overlap_chars, start + 1)
            continue

        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            overlap = current[-overlap_chars:].lstrip()
            current = f"{overlap}\n\n{paragraph}".strip()
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks


def token_estimate(text: str) -> int:
    return max(1, len(text) // 4)
