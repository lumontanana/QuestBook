from langchain_core.documents import Document

from questbook.settings import Settings
from questbook.splitter import split_documents


def test_split_documents_adds_chunk_metadata() -> None:
    settings = Settings(chunk_size=20, chunk_overlap=5)
    documents = [
        Document(
            page_content="uno dos tres cuatro cinco seis siete ocho nueve diez",
            metadata={"source": "book.pdf", "page": 3},
        )
    ]

    chunks = split_documents(documents, settings)

    assert chunks
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[0].metadata["chunk_id"] == "book.pdf:page-3:chunk-0"
