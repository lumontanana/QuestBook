from questbook.pdf_loader import clean_pdf_text, extract_pdf_pages


def test_clean_pdf_text_keeps_paragraphs() -> None:
    raw = "  Line one  \nline two\n\n  New paragraph  \n"

    assert clean_pdf_text(raw) == "Line one line two\n\nNew paragraph"


def test_extract_pdf_pages_returns_empty_list_for_invalid_pdf(tmp_path) -> None:
    invalid_pdf = tmp_path / "invalid.pdf"
    invalid_pdf.write_text("not a pdf", encoding="utf-8")

    assert extract_pdf_pages(invalid_pdf) == []
