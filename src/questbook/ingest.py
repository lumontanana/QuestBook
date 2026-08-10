from pathlib import Path

import structlog
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

from questbook.pdf_loader import extract_pdf_pages
from questbook.providers import get_embeddings
from questbook.settings import Settings, get_settings
from questbook.splitter import split_documents
from questbook.vectorstore import delete_by_source, get_vectorstore

logger = structlog.get_logger(__name__)

CODE_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".md",
    ".txt",
}


def load_text_or_code(path: Path) -> list[Document]:
    docs = TextLoader(str(path), encoding="utf-8", autodetect_encoding=True).load()
    for doc in docs:
        doc.metadata["language"] = path.suffix.lstrip(".")
    return docs


def discover_files(path: Path, include_code: bool = False) -> list[Path]:
    if path.is_file():
        return [path]

    suffixes = {".pdf"}
    if include_code:
        suffixes |= CODE_SUFFIXES
    return sorted(
        file for file in path.rglob("*") if file.is_file() and file.suffix.lower() in suffixes
    )


def ingest_path(
    path: Path, include_code: bool = False, settings: Settings | None = None
) -> tuple[int, int]:
    settings = settings or get_settings()
    files = discover_files(path, include_code=include_code)
    documents: list[Document] = []

    for file in files:
        try:
            if file.suffix.lower() == ".pdf":
                loaded_documents = extract_pdf_pages(file)
            elif include_code:
                loaded_documents = load_text_or_code(file)
            else:
                loaded_documents = []
        except Exception as exc:
            logger.warning("ingest_file_failed", file=str(file), error=str(exc))
            continue

        logger.info("ingest_file_loaded", file=str(file), documents=len(loaded_documents))
        documents.extend(loaded_documents)

    if not documents:
        return 0, 0

    chunks = split_documents(documents, settings)
    vectorstore = get_vectorstore(settings, get_embeddings(settings))
    sources = {str(chunk.metadata["source"]) for chunk in chunks if "source" in chunk.metadata}
    for source in sources:
        delete_by_source(vectorstore, source)
    vectorstore.add_documents(chunks)
    return len(files), len(chunks)
