from langchain_core.embeddings import Embeddings
from langchain_milvus import Milvus

from questbook.settings import Settings


def get_vectorstore(settings: Settings, embeddings: Embeddings) -> Milvus:
    connection_args: dict[str, str] = {"uri": settings.milvus_uri}
    if settings.milvus_token:
        connection_args["token"] = settings.milvus_token

    return Milvus(
        embedding_function=embeddings,
        collection_name=settings.milvus_collection,
        connection_args=connection_args,
        auto_id=True,
    )
