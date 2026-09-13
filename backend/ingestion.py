from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    document_name: str
    text: str
    page: int | None = None


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import fitz
        return "\n".join(page.get_text() for page in fitz.open(path))
    if suffix == ".docx":
        from docx import Document
        return "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
    return path.read_text(encoding="utf-8", errors="replace")


def chunk_text(text: str, document_id: str, document_name: str, size: int = 900, overlap: int = 120) -> list[Chunk]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(start + size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            end = boundary if boundary > start else end
        chunks.append(Chunk(f"{document_id}:{index}", document_id, document_name, normalized[start:end]))
        if end == len(normalized):
            break
        start = max(end - overlap, start + 1)
        index += 1
    return chunks
