from questbook.pdf_loader import clean_pdf_text


def test_clean_pdf_text_keeps_paragraphs() -> None:
    raw = "  Line one  \nline two\n\n  New paragraph  \n"

    assert clean_pdf_text(raw) == "Line one line two\n\nNew paragraph"
