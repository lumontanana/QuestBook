from pathlib import Path

from fastapi.testclient import TestClient

from questbook.api import main
from questbook.settings import Settings


def test_ingest_path_rejects_path_outside_ingest_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "settings",
        Settings(data_dir=tmp_path / "data", ingest_root=tmp_path / "data"),
    )
    client = TestClient(main.app)

    response = client.post("/ingest/path", params={"path": str(tmp_path.parent)})

    assert response.status_code == 400
    assert response.json() == {"detail": "path not allowed"}


def test_ingest_path_accepts_path_inside_ingest_root(tmp_path: Path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True)
    monkeypatch.setattr(main, "settings", Settings(data_dir=data_dir, ingest_root=data_dir))
    monkeypatch.setattr(main, "ingest_path", lambda *args, **kwargs: (0, 0))
    client = TestClient(main.app)

    response = client.post("/ingest/path", params={"path": str(raw_dir)})

    assert response.status_code == 200
    assert response.json()["files"] == 0
