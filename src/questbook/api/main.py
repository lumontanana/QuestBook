from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from questbook.ingest import ingest_path
from questbook.logging import configure_logging
from questbook.models import AskRequest, AskResponse, IngestResponse
from questbook.qa import ask
from questbook.settings import get_settings

settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger(__name__)

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: object, exc: Exception) -> JSONResponse:
    logger.exception("api_unhandled_error", error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "internal error"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "collection": settings.milvus_collection}


@app.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest) -> AskResponse:
    answer, sources = await run_in_threadpool(
        ask,
        payload.question,
        payload.top_k,
        settings,
    )
    return AskResponse(answer=answer, sources=sources)


@app.post("/ingest/path", response_model=IngestResponse)
async def ingest_existing_path(path: str, include_code: bool = False) -> IngestResponse:
    files, chunks = await run_in_threadpool(
        ingest_path,
        Path(path),
        include_code,
        settings,
    )
    return IngestResponse(files=files, chunks=chunks, collection=settings.milvus_collection)
