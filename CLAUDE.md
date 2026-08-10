# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado del trabajo

Antes de empezar, leer `docs/HANDOFF.md`: dice en que punto quedo el trabajo, que decisiones
ya estan tomadas y que esta verificado (para no repetirlo). El diagnostico completo y el plan
por fases estan en `docs/PLAN.md`.

## Proyecto

QuestBook es un sistema RAG sobre una biblioteca local de PDFs (y opcionalmente archivos de codigo/texto): PDF -> extraccion por pagina -> chunks -> embeddings -> Milvus -> pregunta/respuesta con un LLM.

El codigo, los docstrings y los mensajes de usuario estan en castellano sin tildes. Mantener ese estilo al escribir codigo nuevo.

## Comandos

Hay un `Makefile` con la ruta corta: `make setup` (venv + dependencias + `.env`),
`make milvus-up`, `make check`, `make doctor`. `make help` los lista todos.
Los comandos equivalentes en crudo:

```bash
pip install -e ".[dev]"          # instalacion en local (Python 3.10+)

pytest                           # tests (addopts = -q, testpaths = tests)
pytest tests/test_ingest.py::test_discover_pdf_files   # un solo test
ruff check .                     # lint (line-length 100, reglas E,F,I,B,UP)
mypy src                         # tipado (strict = true, plugin pydantic)

docker compose up -d milvus      # solo Milvus en localhost:19530
docker compose up --build        # milvus + api (8000) + streamlit (8501)

questbook ingest-pdf data/raw [--include-code]   # indexar
questbook ask "pregunta"                          # preguntar por CLI
uvicorn questbook.api.main:app --reload           # API
streamlit run apps/streamlit_app.py               # UI de solo consulta
python apps/gradio_app.py                         # UI con subida de PDFs (7860)
```

`mypy` en modo strict es exigente con LangChain: los constructores de proveedores usan `cast(...)` deliberadamente en `providers.py`. Mantener ese patron al anadir proveedores.

## Arquitectura

Todo el pipeline se compone a partir de `Settings` (pydantic-settings, `.env`), que se pasa explicitamente entre modulos. `get_settings()` esta cacheado con `lru_cache`, por lo que **los tests y las funciones publicas aceptan un `settings: Settings | None`** para poder inyectar configuracion sin tocar el singleton. Al anadir codigo nuevo, seguir esa convencion en vez de llamar a `get_settings()` en profundidad.

Modulos en `src/questbook/`:

- `settings.py` — unica fuente de configuracion. Los `Literal` `EmbeddingProvider` / `LlmProvider` definen que proveedores son validos.
- `providers.py` — fabricas `get_embeddings()` / `get_llm()`. Los imports de cada SDK son **perezosos, dentro de la rama** para no forzar dependencias pesadas. Cada funcion termina con un caso por defecto (huggingface para embeddings; ChatOpenAI apuntando a LM Studio/llama.cpp para LLM), asi que un proveedor no reconocido cae en ese camino en vez de fallar.
- `pdf_loader.py` — `extract_pdf_pages()` produce un `Document` por pagina con metadata `source`, `book_title`, `page`; las paginas vacias se descartan.
- `splitter.py` — `RecursiveCharacterTextSplitter` y asignacion de `chunk_index` / `chunk_id` (`{source}:page-{page}:chunk-{index}`). El `chunk_id` es el identificador que viaja hasta las respuestas de la API.
- `ingest.py` — descubrimiento de ficheros (`discover_files`, solo `.pdf` salvo `include_code=True`, que anade `CODE_SUFFIXES`), carga, split y `add_documents` en Milvus.
- `vectorstore.py` — `langchain_milvus.Milvus` con `auto_id=True`; la coleccion se crea sola en la primera insercion.
- `qa.py` — retriever + `PROMPT` + LLM. El prompt fuerza responder solo con el contexto recuperado. `ask()` devuelve `(answer, list[Source])`; la respuesta se extrae con `getattr(result, "content", str(result))` porque el LLM puede ser `BaseChatModel` o `LLM`.
- `models.py` — esquemas Pydantic compartidos por API y UIs.
- `api/main.py`, `cli.py`, `apps/` — cuatro superficies (API, CLI, Streamlit, Gradio) que solo orquestan `ingest_path()` y `ask()`. La logica nueva va en los modulos del pipeline, no en las superficies.

## Detalles que no son obvios

- `mypy src` **falla hoy en una instalacion limpia**: `python_version = "3.10"` choca con los
  stubs de numpy, que usan sintaxis de 3.12+. No es un error del codigo (con
  `--python-version 3.13` pasa limpio); esta pendiente de corregir en la fase 1 del plan.
- Los defaults reales son **huggingface + LM Studio local** (`settings.py` y `.env.example`), no OpenAI. El README describe el flujo con OpenAI y esta desactualizado en ese punto; tambien omite `apps/gradio_app.py`.
- `code_parser.py` (tree-sitter, simbolos Python) existe pero **no esta conectado** al pipeline de ingesta; los ficheros de codigo se cargan hoy con `TextLoader`.
- Streamlit es solo consulta; Gradio si permite subir PDFs (los copia a `data_dir/raw` y reindexa esa carpeta entera). `docker-compose.yml` no levanta Gradio.
- Cambiar `EMBEDDING_MODEL` cambia la dimension de los vectores: hay que recrear o reindexar la coleccion de Milvus.
- Milvus corre en modo standalone con etcd embebido (`embedEtcd.yaml`, `user.yaml`) y persiste en `./volumes/milvus`.
- En Docker, la API y Streamlit apuntan a `host.docker.internal` para LM Studio/llama.cpp, que corren en el host.
- `data/raw` y `data/processed` estan versionados solo con `.gitkeep`; los PDFs no se commitean.
