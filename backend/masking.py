"""Deterministic PII masking. Original values never leave this process."""

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable


PATTERNS = (
    ("EMAIL", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("DATE_OF_BIRTH", re.compile(r"\b(?:\d{1,2}[/-]){2}\d{2,4}\b")),
    ("MRN", re.compile(r"\b(?:MRN|medical record|patient)\s*[:#-]?\s*[A-Z0-9-]{4,}\b", re.I)),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]*?){13,19}\b")),
    ("PHONE", re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")),
)


@dataclass(frozen=True)
class MaskMatch:
    kind: str
    token: str
    start: int
    end: int


def _token(kind: str, value: str, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}:{kind}:{value.casefold()}".encode()).hexdigest()[:10].upper()
    return f"<{kind}_{digest}>"


def mask_text(text: str, salt: str = "vaultrag-local", additional_matches: Iterable[MaskMatch] = ()) -> tuple[str, list[MaskMatch]]:
    matches: list[MaskMatch] = []
    for kind, pattern in PATTERNS:
        for match in pattern.finditer(text):
            matches.append(MaskMatch(kind, _token(kind, match.group(), salt), match.start(), match.end()))
    for match in additional_matches:
        token = match.token or _token(match.kind, text[match.start:match.end], salt)
        matches.append(MaskMatch(match.kind, token, match.start, match.end))
    matches.sort(key=lambda item: (item.start, -(item.end - item.start)))
    accepted: list[MaskMatch] = []
    cursor = -1
    for match in matches:
        if match.start >= cursor:
            accepted.append(match)
            cursor = match.end
    for match in reversed(accepted):
        text = text[:match.start] + match.token + text[match.end:]
    return text, accepted
