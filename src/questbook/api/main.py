from pathlib import Path

from fastapi import FastAPI

from questbook.ingest import ingest_path
from questbook.logging import configure_logging
from questbook.models import AskRequest, AskResponse, IngestResponse
from questbook.qa import ask
from questbook.settings import get_settings

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "collection": settings.milvus_collection}


@app.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    answer, sources = ask(payload.question, payload.top_k, settings=settings)
    return AskResponse(answer=answer, sources=sources)


@app.post("/ingest/path", response_model=IngestResponse)
def ingest_existing_path(path: str, include_code: bool = False) -> IngestResponse:
    files, chunks = ingest_path(Path(path), include_code=include_code, settings=settings)
    return IngestResponse(files=files, chunks=chunks, collection=settings.milvus_collection)
