# QuestBook

QuestBook es un proyecto RAG para hacer preguntas sobre una biblioteca local de libros en PDF.

El flujo principal es:

```text
PDF -> extraccion de texto -> chunks -> embeddings OpenAI -> Milvus -> pregunta/respuesta
```

La idea es que tus libros vivan en `data/raw`, se indexen una vez en Milvus y luego puedas preguntar sobre ellos desde una API, una CLI o una interfaz web simple.

## Objetivo

Construir un sistema que permita:

- Leer libros en formato PDF.
- Extraer el texto pagina por pagina.
- Dividir el contenido en chunks de texto.
- Generar embeddings con OpenAI.
- Guardar los vectores y la metadata en Milvus.
- Reindexar libros sin duplicar chunks existentes.
- Recuperar los chunks mas relevantes para una pregunta.
- Responder usando un modelo LLM con contexto del libro.

## Stack

- Python 3.10+
- FastAPI para la API HTTP.
- Typer para la CLI.
- Streamlit para una UI simple de pregunta/respuesta.
- pypdf para extraccion de texto desde PDFs.
- LangChain para documentos, splitters, embeddings, retrievers y modelos.
- OpenAI para embeddings y respuestas.
- Milvus como base de datos vectorial.
- Pydantic y pydantic-settings para configuracion.
- Rich y structlog para consola/logging.
- Pytest, Ruff y mypy para calidad.
- Docker Compose para levantar servicios.

## Arquitectura

```text
data/raw/libro.pdf
        |
        v
PDF extractor
        |
        v
Text splitter
        |
        v
OpenAI embeddings
        |
        v
Milvus collection
        |
        v
Retriever
        |
        v
OpenAI LLM
        |
        v
Respuesta + fuentes
```

## Estructura

```text
QuestBook/
|-- apps/
|   `-- streamlit_app.py
|-- data/
|   |-- raw/
|   `-- processed/
|-- src/
|   `-- questbook/
|       |-- api/
|       |   |-- __init__.py
|       |   `-- main.py
|       |-- __init__.py
|       |-- cli.py
|       |-- code_parser.py
|       |-- ingest.py
|       |-- logging.py
|       |-- models.py
|       |-- pdf_loader.py
|       |-- providers.py
|       |-- qa.py
|       |-- settings.py
|       |-- splitter.py
|       `-- vectorstore.py
|-- tests/
|-- .env.example
|-- Dockerfile
|-- docker-compose.yml
|-- embedEtcd.yaml
|-- pyproject.toml
`-- user.yaml
```

## Configuracion

Copia el archivo de ejemplo:

```powershell
Copy-Item .env.example .env
```

Variables importantes:

```env
OPENAI_API_KEY=tu_api_key
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-large
MILVUS_URI=http://localhost:19530
MILVUS_COLLECTION=questbook_documents
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
TOP_K=4
```

## Instalacion Local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Docker

Levantar Milvus:

```powershell
docker compose up -d milvus
```

Levantar todo:

```powershell
docker compose up --build
```

Servicios:

```text
Milvus:    http://localhost:19530
API:       http://localhost:8000
Streamlit: http://localhost:8501
```

## Uso

Coloca tus PDFs en:

```text
data/raw/
```

Indexa los libros:

```powershell
questbook ingest-pdf data/raw
```

Si vuelves a indexar un PDF ya existente, QuestBook reemplaza los chunks anteriores de ese archivo en Milvus antes de insertar los nuevos. Esto evita duplicados al reindexar.

Si un PDF esta corrupto o no se puede leer, se omite y la ingesta continua con el resto de archivos.

Pregunta desde la CLI:

```powershell
questbook ask "Cual es la idea principal del libro?"
```

Levanta la API:

```powershell
uvicorn questbook.api.main:app --reload
```

Levanta la UI:

```powershell
streamlit run apps/streamlit_app.py
```

## API

Healthcheck:

```http
GET /health
```

Ingestar una carpeta local:

```http
POST /ingest/path?path=data/raw
```

Preguntar:

```http
POST /ask
```

Body:

```json
{
  "question": "Que explica el libro sobre inteligencia artificial?",
  "top_k": 4
}
```

Respuesta:

```json
{
  "answer": "Respuesta generada con el contexto recuperado...",
  "sources": [
    {
      "source": "data/raw/libro.pdf",
      "page": 12,
      "chunk_id": "data/raw/libro.pdf:page-12:chunk-3",
      "content": "Fragmento usado como fuente..."
    }
  ]
}
```

## Flujo Recomendado

1. Copia tus PDFs a `data/raw`.
2. Arranca Milvus con Docker.
3. Ejecuta la ingesta.
4. Haz preguntas desde CLI, API o Streamlit.
5. Reindexa cuando agregues libros nuevos.

## Calidad

```powershell
pytest
ruff check .
mypy src
```

## Notas

- El modelo `text-embedding-3-large` no se descarga localmente; se consume mediante la API de OpenAI.
- Milvus guarda los vectores y la metadata de cada chunk.
- Cada chunk guarda metadata como `source`, `book_title`, `page`, `chunk_index` y `chunk_id`.
- `chunk_index` se reinicia por archivo y pagina, por ejemplo `libro.pdf:page-3:chunk-0`.
- Reindexar un archivo reemplaza sus chunks previos en Milvus.
- La UI no permite subir PDFs: la biblioteca se administra desde `data/raw`.
- Si cambias el modelo de embeddings, conviene recrear o reindexar la coleccion de Milvus.
