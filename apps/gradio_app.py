from pathlib import Path

import gradio as gr

from questbook.ingest import ingest_path
from questbook.qa import ask
from questbook.settings import get_settings

settings = get_settings()


def ingest_files(files: list[str] | None) -> str:
    if not files:
        return "Sube al menos un PDF."

    raw_dir = settings.data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        source = Path(file)
        target = raw_dir / source.name
        target.write_bytes(source.read_bytes())

    count, chunks = ingest_path(raw_dir, settings=settings)
    return f"Indexados {chunks} chunks desde {count} archivo(s)."


def answer_question(question: str, top_k: int) -> tuple[str, str]:
    answer, sources = ask(question, top_k=top_k, settings=settings)
    rendered_sources = "\n\n".join(
        f"{source.source} pagina {source.page}\n{source.content[:500]}" for source in sources
    )
    return answer, rendered_sources


with gr.Blocks(title=settings.app_name) as demo:
    gr.Markdown(f"# {settings.app_name}")
    with gr.Tab("Preguntar"):
        question = gr.Textbox(label="Pregunta", lines=2)
        top_k = gr.Slider(1, 10, value=settings.top_k, step=1, label="Top K")
        ask_button = gr.Button("Responder", variant="primary")
        answer = gr.Textbox(label="Respuesta", lines=8)
        sources = gr.Textbox(label="Fuentes", lines=10)
        ask_button.click(answer_question, inputs=[question, top_k], outputs=[answer, sources])

    with gr.Tab("Indexar PDFs"):
        files = gr.File(label="PDFs", file_count="multiple", file_types=[".pdf"])
        ingest_button = gr.Button("Indexar", variant="primary")
        result = gr.Textbox(label="Resultado")
        ingest_button.click(ingest_files, inputs=[files], outputs=[result])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
