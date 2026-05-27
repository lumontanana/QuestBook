from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

from questbook.pdf_loader import extract_pdf_pages
from questbook.providers import get_embeddings
from questbook.settings import Settings, get_settings
from questbook.splitter import split_documents
from questbook.vectorstore import get_vectorstore

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


def validate_ingest_path(path: Path, root: Path) -> Path:
    resolved = path.expanduser().resolve()
    resolved_root = root.expanduser().resolve()

    if not resolved.is_relative_to(resolved_root):
        raise ValueError("path not allowed")

    return resolved


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
    path = validate_ingest_path(path, settings.ingest_root)
    files = discover_files(path, include_code=include_code)
    documents: list[Document] = []

    for file in files:
        if file.suffix.lower() == ".pdf":
            documents.extend(extract_pdf_pages(file))
        elif include_code:
            documents.extend(load_text_or_code(file))

    if not documents:
        return 0, 0

    chunks = split_documents(documents, settings)
    vectorstore = get_vectorstore(settings, get_embeddings(settings))
    vectorstore.add_documents(chunks)
    return len(files), len(chunks)
