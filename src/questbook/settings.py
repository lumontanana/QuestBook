from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

EmbeddingProvider = Literal["openai", "cohere", "huggingface", "jina"]
LlmProvider = Literal["openai", "cohere", "huggingface", "lmstudio", "llamacpp"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "QuestBook"
    app_env: str = "local"
    log_level: str = "INFO"

    milvus_uri: str = "http://localhost:19530"
    milvus_token: str | None = None
    milvus_collection: str = "questbook_documents"

    embedding_provider: EmbeddingProvider = "huggingface"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_provider: LlmProvider = "lmstudio"
    llm_model: str = "local-model"

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    cohere_api_key: str | None = None
    jina_api_key: str | None = None
    huggingfacehub_api_token: str | None = None
    lmstudio_base_url: str = "http://localhost:1234/v1"
    llamacpp_base_url: str = "http://localhost:8080/v1"

    data_dir: Path = Field(default=Path("data"))
    ingest_root: Path = Field(default=Path("data"))
    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 4


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
