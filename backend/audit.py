"""Append-only, content-redacted operational events for local troubleshooting."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .masking import mask_text


class AuditLogger:
    """Write useful operational metadata without persisting raw user content."""

    def __init__(self, log_dir: Path, enabled: bool = True):
        self.log_dir = log_dir
        self.enabled = enabled
        self.path = log_dir / "events.jsonl"

    def record(self, event: str, **details: Any) -> None:
        if not self.enabled:
            return
        self.log_dir.mkdir(parents=True, exist_ok=True)
        safe_details: dict[str, Any] = {}
        for key, value in details.items():
            if isinstance(value, str) and key in {"query", "text", "error"}:
                safe_details[key], _ = mask_text(value)
            elif isinstance(value, (str, int, float, bool)) or value is None:
                safe_details[key] = value
            else:
                safe_details[key] = str(value)
        payload = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, "details": safe_details}
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=True) + "\n")
