from slack_kb.chunking import chunk_text, normalize_text


def test_normalize_text_removes_noise() -> None:
    assert normalize_text(" hello   world \n\n\n next ") == "hello world\n\n next"


def test_chunk_text_preserves_overlap() -> None:
    text = "A" * 80 + "\n\n" + "B" * 80
    chunks = chunk_text(text, max_chars=100, overlap_chars=10)
    assert len(chunks) == 2
    assert chunks[1].startswith("A" * 10)
