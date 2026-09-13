from backend.ingestion import chunk_text
from backend.masking import mask_text


def test_masking_is_deterministic_and_reversible_in_shape():
    first, matches = mask_text("Contact Ada at ada@example.com or 555-123-4567")
    second, _ = mask_text("Contact Ada at ada@example.com or 555-123-4567")
    assert first == second
    assert "ada@example.com" not in first
    assert len(matches) == 2
    assert "<EMAIL_" in first and "<PHONE_" in first


def test_chunking_preserves_document_identity():
    chunks = chunk_text("word " * 500, "doc-1", "case.txt", size=100, overlap=10)
    assert len(chunks) > 1
    assert all(chunk.document_id == "doc-1" for chunk in chunks)
