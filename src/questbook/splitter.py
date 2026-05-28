from collections import defaultdict
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from questbook.settings import Settings


def split_documents(documents: list[Document], settings: Settings) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    counters: dict[tuple[str, Any], int] = defaultdict(int)
    for chunk in chunks:
        source = chunk.metadata.get("source", "document")
        page = chunk.metadata.get("page", "unknown")
        index = counters[(source, page)]
        counters[(source, page)] += 1
        chunk.metadata["chunk_index"] = index
        chunk.metadata["chunk_id"] = f"{source}:page-{page}:chunk-{index}"

    return chunks
