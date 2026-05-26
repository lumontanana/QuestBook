from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from questbook.ingest import ingest_path
from questbook.logging import configure_logging
from questbook.qa import ask
from questbook.settings import get_settings

app = typer.Typer(help="QuestBook: pregunta sobre tus PDFs con RAG y Milvus.")
console = Console()


@app.callback()
def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command("ingest-pdf")
def ingest_pdf(
    path: Annotated[Path, typer.Argument(help="PDF o carpeta con PDFs.")],
    include_code: Annotated[
        bool, typer.Option(help="Tambien indexa archivos de codigo/texto.")
    ] = False,
) -> None:
    files, chunks = ingest_path(path, include_code=include_code)
    console.print(f"[green]Indexados {chunks} chunks desde {files} archivo(s).[/green]")


@app.command("ask")
def ask_command(
    question: Annotated[str, typer.Argument(help="Pregunta sobre los documentos indexados.")],
    top_k: Annotated[int | None, typer.Option(help="Numero de fragmentos recuperados.")] = None,
) -> None:
    answer, sources = ask(question, top_k)
    console.print(answer)

    table = Table(title="Fuentes")
    table.add_column("Archivo")
    table.add_column("Pagina")
    table.add_column("Fragmento")
    for source in sources:
        table.add_row(source.source, str(source.page), source.content[:180].replace("\n", " "))
    console.print(table)
