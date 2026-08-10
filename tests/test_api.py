from pathlib import Path

from fastapi.testclient import TestClient

from questbook.api import main
from questbook.models import Source


def test_ask_endpoint_returns_answer(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "ask",
        lambda *args, **kwargs: (
            "respuesta",
            [Source(source="book.pdf", page=1, chunk_id="chunk-1", content="texto")],
        ),
    )
    client = TestClient(main.app)

    response = client.post("/ask", json={"question": "Que dice el libro?", "top_k": 4})

    assert response.status_code == 200
    assert response.json()["answer"] == "respuesta"
    assert response.json()["sources"][0]["source"] == "book.pdf"


def test_ask_endpoint_rejects_question_over_limit() -> None:
    client = TestClient(main.app)

    response = client.post("/ask", json={"question": "x" * 2001})

    assert response.status_code == 422


def test_ingest_path_endpoint_returns_counts(tmp_path: Path, monkeypatch) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    monkeypatch.setattr(main, "ingest_path", lambda *args, **kwargs: (2, 10))
    client = TestClient(main.app)

    response = client.post("/ingest/path", params={"path": str(raw_dir)})

    assert response.status_code == 200
    assert response.json()["files"] == 2
    assert response.json()["chunks"] == 10


def test_unhandled_exception_handler_returns_json() -> None:
    client = TestClient(main.app, raise_server_exceptions=False)

    @main.app.get("/_test-error")
    def test_error() -> None:
        raise RuntimeError("boom")

    response = client.get("/_test-error")

    assert response.status_code == 500
    assert response.json() == {"detail": "internal error"}
