import logging
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .audit import AuditLogger
from .config import get_settings
from .generation import RetrievalOnlyGenerator, TransformersGenerator
from .ingestion import chunk_text, extract_text
from .masking import MaskMatch, mask_text
from .ner import LocalNER
from .retrieval import LocalIndex, new_document_id
from .schemas import DocumentSummary, HealthResponse, QueryRequest, QueryResponse, UploadResponse

settings = get_settings()
logging.basicConfig(level=settings.vaultrag_log_level)
index = LocalIndex(settings.vaultrag_index_dir)
audit = AuditLogger(settings.vaultrag_data_dir / "logs", settings.vaultrag_audit_enabled)
ner = LocalNER(settings.vaultrag_ner_model) if settings.vaultrag_enable_ner and settings.vaultrag_ner_model else None
generator = TransformersGenerator(settings.vaultrag_generation_model, settings.vaultrag_max_new_tokens) if settings.vaultrag_enable_generation else RetrievalOnlyGenerator()
app = FastAPI(title="VaultRAG Local API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:1420", "tauri://localhost"], allow_methods=["*"], allow_headers=["*"])


def _mask_for_context(text: str) -> tuple[str, list[MaskMatch]]:
    additional: list[MaskMatch] = []
    if ner is not None:
        for match in ner.detect(text):
            additional.append(MaskMatch(match.kind, "", match.start, match.end))
    return mask_text(text, additional_matches=additional)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="local", documents=len({chunk.document_id for chunk in index.chunks}), chunks=len(index.chunks), generation_enabled=settings.vaultrag_enable_generation, generation_mode="local-transformers" if settings.vaultrag_enable_generation else "retrieval-only", masking_mode="regex+local-ner" if ner else "regex", index_backend=index.backend_name)


@app.get("/api/documents", response_model=list[DocumentSummary])
def documents() -> list[DocumentSummary]:
    grouped: dict[str, dict] = {}
    for chunk in index.chunks:
        item = grouped.setdefault(chunk.document_id, {"id": chunk.document_id, "name": chunk.document_name, "chunks": 0})
        item["chunks"] += 1
    return [DocumentSummary(**item) for item in grouped.values()]


@app.post("/api/documents", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".md", ".pdf", ".docx"}:
        raise HTTPException(415, "Supported formats: TXT, MD, PDF, DOCX")
    payload = await file.read()
    if len(payload) > settings.vaultrag_max_file_mb * 1024 * 1024:
        raise HTTPException(413, "Document exceeds the configured size limit")
    document_id = new_document_id()
    path = settings.vaultrag_upload_dir / f"{document_id}{suffix}"
    path.write_bytes(payload)
    extracted_text = extract_text(path)
    chunks = chunk_text(extracted_text, document_id, file.filename or path.name)
    if not chunks:
        path.unlink(missing_ok=True)
        raise HTTPException(422, "No readable text found in document")
    chunks_added = index.add(chunks)
    audit.record("document_indexed", document_id=document_id, filename=file.filename or path.name, chunks=chunks_added, characters=len(extracted_text))
    return UploadResponse(id=document_id, name=file.filename or path.name, chunks_added=chunks_added, characters_extracted=len(extracted_text))


@app.post("/api/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    masked_query, query_matches = _mask_for_context(request.query)
    results = index.search(masked_query, request.top_k)
    masked_results = []
    for item in results:
        safe_text, _ = _mask_for_context(item["chunk"]["text"])
        masked_item = {**item, "chunk": {**item["chunk"], "text": safe_text}}
        masked_results.append(masked_item)
    context = "\n\n".join(item["chunk"]["text"] for item in masked_results)
    generation = generator.generate(masked_query, context[:12000])
    audit.record("query_completed", query=masked_query, masked_entities=len(query_matches), results=len(masked_results), mode=generation.mode)
    return QueryResponse(answer=generation.answer, query=masked_query, masked_entities=len(query_matches), sources=masked_results, context_preview=context[:4000], generation_mode=generation.mode)


@app.delete("/api/documents")
def clear_documents() -> dict:
    index.clear()
    for path in settings.vaultrag_upload_dir.iterdir():
        if path.is_file():
            path.unlink()
    audit.record("vault_cleared")
    return {"cleared": True}
