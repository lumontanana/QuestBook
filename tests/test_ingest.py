from pathlib import Path

from questbook.ingest import discover_files


def test_discover_pdf_files(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    txt = tmp_path / "notes.txt"
    pdf.write_text("fake", encoding="utf-8")
    txt.write_text("notes", encoding="utf-8")

    assert discover_files(tmp_path) == [pdf]
    assert discover_files(tmp_path, include_code=True) == [txt, pdf]
