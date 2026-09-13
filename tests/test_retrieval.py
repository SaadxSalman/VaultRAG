from backend.ingestion import chunk_text
from backend.retrieval import LocalIndex


def test_index_round_trips_metadata_and_returns_rank(tmp_path):
    index = LocalIndex(tmp_path / "index")
    chunks = chunk_text("The claimant's appointment was moved to Tuesday.", "doc-1", "notes.txt", size=200)
    assert index.add(chunks) == 1
    results = index.search("appointment Tuesday", top_k=3)
    assert results[0]["rank"] == 1
    assert results[0]["chunk"]["document_name"] == "notes.txt"

    restored = LocalIndex(tmp_path / "index")
    assert restored.backend_name == "tfidf-local"
    assert restored.search("claimant appointment", top_k=1)[0]["chunk"]["id"] == chunks[0].id


def test_empty_index_is_safe(tmp_path):
    index = LocalIndex(tmp_path / "index")
    assert index.search("anything", top_k=5) == []
    index.clear()
    assert index.chunks == []
