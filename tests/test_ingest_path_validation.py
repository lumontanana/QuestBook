from pathlib import Path

import pytest

from questbook.ingest import validate_ingest_path


def test_validate_ingest_path_allows_child_path(tmp_path: Path) -> None:
    root = tmp_path / "data"
    child = root / "raw"
    child.mkdir(parents=True)

    assert validate_ingest_path(child, root) == child.resolve()


def test_validate_ingest_path_rejects_parent_path(tmp_path: Path) -> None:
    root = tmp_path / "data"
    root.mkdir()

    with pytest.raises(ValueError, match="path not allowed"):
        validate_ingest_path(tmp_path, root)
