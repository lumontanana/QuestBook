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

    for index, chunk in enumerate(chunks):
        source = chunk.metadata.get("source", "document")
        page = chunk.metadata.get("page", "unknown")
        chunk.metadata["chunk_index"] = index
        chunk.metadata["chunk_id"] = f"{source}:page-{page}:chunk-{index}"

    return chunks
