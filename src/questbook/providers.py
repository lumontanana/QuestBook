from collections.abc import Callable
from typing import Any, cast

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import LLM

from questbook.settings import Settings


def get_embeddings(settings: Settings) -> Embeddings:
    provider = settings.embedding_provider

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        openai_kwargs: dict[str, Any] = {
            "model": settings.embedding_model,
            "api_key": settings.openai_api_key,
            "base_url": settings.openai_base_url,
        }
        return cast(
            Embeddings,
            OpenAIEmbeddings(**openai_kwargs),
        )

    if provider == "cohere":
        from langchain_cohere import CohereEmbeddings

        return cast(
            Embeddings,
            CohereEmbeddings(
                client=None,
                async_client=None,
                model=settings.embedding_model,
                cohere_api_key=settings.cohere_api_key,
            ),
        )

    if provider == "jina":
        from langchain_community.embeddings import JinaEmbeddings

        return cast(
            Embeddings,
            JinaEmbeddings(
                session=None,
                jina_api_key=settings.jina_api_key,
                model_name=settings.embedding_model,
            ),
        )

    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=settings.embedding_model)


def get_llm(settings: Settings) -> BaseChatModel | LLM:
    provider = settings.llm_provider

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0,
        )

    if provider == "cohere":
        from langchain_cohere import ChatCohere

        return ChatCohere(
            model=settings.llm_model,
            cohere_api_key=settings.cohere_api_key,
            temperature=0,
        )

    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEndpoint

        return cast(
            LLM,
            HuggingFaceEndpoint(
                model=settings.llm_model,
                repo_id=settings.llm_model,
                huggingfacehub_api_token=settings.huggingfacehub_api_token,
                temperature=0.1,
                max_new_tokens=700,
            ),
        )

    from langchain_openai import ChatOpenAI

    base_url_by_provider: dict[str, Callable[[], str]] = {
        "lmstudio": lambda: settings.lmstudio_base_url,
        "llamacpp": lambda: settings.llamacpp_base_url,
    }
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key or "not-needed",
        base_url=base_url_by_provider[provider](),
        temperature=0,
    )
