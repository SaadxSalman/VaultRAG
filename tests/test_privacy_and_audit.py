import json

from backend.audit import AuditLogger
from backend.masking import MaskMatch, mask_text


def test_more_specific_identifier_wins_over_phone_pattern():
    masked, matches = mask_text("SSN 123-45-6789")
    assert "123-45-6789" not in masked
    assert matches[0].kind == "SSN"
    assert matches[0].token.startswith("<SSN_")


def test_ner_span_is_masked_with_the_same_pipeline():
    masked, matches = mask_text("Review Ada Lovelace", additional_matches=[MaskMatch("PERSON", "", 7, 19)])
    assert "Ada Lovelace" not in masked
    assert matches[0].kind == "PERSON"


def test_audit_log_masks_sensitive_detail(tmp_path):
    logger = AuditLogger(tmp_path)
    logger.record("query_completed", query="Contact ada@example.com", results=2)
    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8"))
    assert "ada@example.com" not in json.dumps(event)
    assert "<EMAIL_" in event["details"]["query"]
    assert event["details"]["results"] == 2
