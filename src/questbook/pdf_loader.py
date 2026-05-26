from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader


def clean_pdf_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    paragraphs: list[str] = []
    current: list[str] = []

    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)

    if current:
        paragraphs.append(" ".join(current))

    return "\n\n".join(paragraphs).strip()


def extract_pdf_pages(path: Path) -> list[Document]:
    reader = PdfReader(str(path))
    documents: list[Document] = []
    book_title = path.stem

    for index, page in enumerate(reader.pages, start=1):
        text = clean_pdf_text(page.extract_text() or "")
        if not text:
            continue

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(path),
                    "book_title": book_title,
                    "page": index,
                },
            )
        )

    return documents
