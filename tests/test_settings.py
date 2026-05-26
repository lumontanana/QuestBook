from questbook.settings import Settings


def test_default_settings() -> None:
    settings = Settings()

    assert settings.app_name == "QuestBook"
    assert settings.milvus_collection
    assert settings.chunk_size > settings.chunk_overlap
