from pathlib import Path

from langchain_core.documents import Document

from questbook import ingest
from questbook.settings import Settings
from questbook.vectorstore import escape_milvus_string


class FakeVectorStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def delete(self, expr: str) -> None:
        self.calls.append(("delete", expr))

    def add_documents(self, documents: list[Document]) -> None:
        self.calls.append(("add_documents", documents))


def test_ingest_deletes_existing_source_before_adding_chunks(tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "book.pdf"
    pdf.write_text("fake", encoding="utf-8")
    document = Document(page_content="texto", metadata={"source": str(pdf), "page": 1})
    fake_vectorstore = FakeVectorStore()

    monkeypatch.setattr(ingest, "extract_pdf_pages", lambda _: [document])
    monkeypatch.setattr(ingest, "split_documents", lambda documents, _: documents)
    monkeypatch.setattr(ingest, "get_embeddings", lambda _: object())
    monkeypatch.setattr(ingest, "get_vectorstore", lambda *_: fake_vectorstore)

    files, chunks = ingest.ingest_path(pdf, settings=Settings())

    assert (files, chunks) == (1, 1)
    assert fake_vectorstore.calls[0] == ("delete", f'source == "{escape_milvus_string(str(pdf))}"')
    assert fake_vectorstore.calls[1] == ("add_documents", [document])
