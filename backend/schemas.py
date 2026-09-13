"""Public API contracts kept separate from HTTP route implementations."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    mask_query: bool = True


class SourceChunk(BaseModel):
    id: str
    document_id: str
    document_name: str
    text: str
    page: int | None = None


class SourceResult(BaseModel):
    rank: int
    score: float
    chunk: SourceChunk


class QueryResponse(BaseModel):
    answer: str
    query: str
    masked_entities: int
    sources: list[SourceResult]
    context_preview: str
    generation_mode: str


class UploadResponse(BaseModel):
    id: str
    name: str
    chunks_added: int
    characters_extracted: int


class DocumentSummary(BaseModel):
    id: str
    name: str
    chunks: int


class HealthResponse(BaseModel):
    status: str
    service: str
    documents: int
    chunks: int
    generation_enabled: bool
    generation_mode: str
    masking_mode: str
    index_backend: str
