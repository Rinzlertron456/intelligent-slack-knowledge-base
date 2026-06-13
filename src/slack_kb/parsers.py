from __future__ import annotations

import io
from pathlib import PurePath

import httpx
import trafilatura
from bs4 import BeautifulSoup
from docx import Document
from pypdf import PdfReader

from slack_kb.chunking import normalize_text
from slack_kb.models import DocumentPayload

SUPPORTED_FILE_TYPES = {"pdf", "docx", "txt", "md", "markdown"}


def parse_file(filename: str, content: bytes, source_url: str | None = None) -> DocumentPayload:
    suffix = PurePath(filename).suffix.lower().lstrip(".")
    if suffix not in SUPPORTED_FILE_TYPES:
        raise ValueError(f"Unsupported file type: .{suffix or 'unknown'}")

    if suffix == "pdf":
        reader = PdfReader(io.BytesIO(content))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix == "docx":
        document = Document(io.BytesIO(content))
        text = "\n\n".join(paragraph.text for paragraph in document.paragraphs)
    else:
        text = content.decode("utf-8", errors="replace")

    clean = normalize_text(text)
    if not clean:
        raise ValueError("No readable text was extracted from the file")
    return DocumentPayload(
        title=filename,
        source_type=suffix,
        content=clean,
        source_url=source_url,
    )


def parse_url(url: str) -> DocumentPayload:
    response = httpx.get(
        url,
        timeout=20,
        follow_redirects=True,
        headers={"User-Agent": "IntelligentSlackKnowledgeBase/0.1"},
    )
    response.raise_for_status()
    extracted = trafilatura.extract(
        response.text,
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    )
    if not extracted:
        extracted = BeautifulSoup(response.text, "html.parser").get_text("\n")
    clean = normalize_text(extracted or "")
    if not clean:
        raise ValueError("No readable text was extracted from the URL")
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    return DocumentPayload(title=title, source_type="url", content=clean, source_url=url)


def parse_plain_text(text: str, *, title: str = "Slack note") -> DocumentPayload:
    clean = normalize_text(text)
    if not clean:
        raise ValueError("Text content is empty")
    return DocumentPayload(title=title, source_type="text", content=clean)
