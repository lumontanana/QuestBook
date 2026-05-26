from typing import Any

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from questbook.models import Source
from questbook.providers import get_embeddings, get_llm
from questbook.settings import Settings, get_settings
from questbook.vectorstore import get_vectorstore

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente de estudio. Responde solo con la informacion del contexto. "
            "Si el contexto no alcanza, dilo claramente y sugiere que documentos faltan.",
        ),
        ("human", "Pregunta: {question}\n\nContexto:\n{context}"),
    ]
)


def format_docs(docs: list[Document]) -> str:
    return "\n\n".join(
        (
            f"[Fuente: {doc.metadata.get('source')} "
            f"pagina {doc.metadata.get('page')}]\n{doc.page_content}"
        )
        for doc in docs
    )


def docs_to_sources(docs: list[Document]) -> list[Source]:
    return [
        Source(
            source=str(doc.metadata.get("source", "desconocido")),
            page=doc.metadata.get("page"),
            chunk_id=doc.metadata.get("chunk_id"),
            content=doc.page_content,
        )
        for doc in docs
    ]


def ask(
    question: str, top_k: int | None = None, settings: Settings | None = None
) -> tuple[str, list[Source]]:
    settings = settings or get_settings()
    embeddings = get_embeddings(settings)
    vectorstore = get_vectorstore(settings, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k or settings.top_k})
    llm = get_llm(settings)

    docs = retriever.invoke(question)
    chain: Any = (
        {"context": lambda _: format_docs(docs), "question": RunnablePassthrough()} | PROMPT | llm
    )
    result = chain.invoke(question)
    answer = getattr(result, "content", str(result))
    return answer, docs_to_sources(docs)
