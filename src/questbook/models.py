from pydantic import BaseModel, Field


class Source(BaseModel):
    source: str
    page: int | None = None
    chunk_id: str | None = None
    content: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


class IngestResponse(BaseModel):
    files: int
    chunks: int
    collection: str
