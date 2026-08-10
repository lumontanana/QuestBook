# Estado del trabajo — punto de continuacion

Ultima actualizacion: 2026-08-10
Ultimo commit de contenido: fusion de `feature/openai-embeddings-milvus` en `master` (`0812c2b`).

Este documento existe para poder retomar el trabajo en otra maquina sin repetir el analisis.
El diagnostico completo y el plan por fases estan en [PLAN.md](PLAN.md).

---

## 1. Donde nos quedamos

**Fase 0 del plan terminada. La fase 1 no se ha empezado: no se ha tocado ni una linea de
`src/`.** Todo el trabajo hecho hasta ahora es de diagnostico, herramientas y documentacion.

Completado:

- Rama `feature/openai-embeddings-milvus` fusionada en `master` con fast-forward.
- Diagnostico verificado ejecutando el codigo contra un Milvus real (no solo lectura de codigo).
- `Makefile` con instalacion, calidad, Milvus, uso, Docker y `make doctor`.
- `CLAUDE.md` con arquitectura y trampas del proyecto.
- `docs/PLAN.md` con 17 hallazgos y un plan en 6 fases.

Siguiente paso: **fase 1 del plan** (H1 perdida de datos, H2 mypy, H3 dependencias).

---

## 2. Puesta en marcha en la maquina nueva

```bash
git clone <repo> && cd QuestBook
make setup        # crea .venv, instala en modo editable y genera .env
make milvus-up    # levanta Milvus en Docker y espera al healthcheck
make doctor       # confirma venv, .env, Milvus y LM Studio
```

Nada de lo necesario para arrancar esta en git y hay que regenerarlo: `.env` (lo crea
`make env` desde `.env.example`), `.venv/` y `volumes/milvus/` con los datos indexados.
La coleccion de Milvus de esta maquina se dejo **vacia** a proposito: los datos de prueba se
borraron al terminar de verificar.

---

## 3. Decisiones ya tomadas (no volver a discutirlas)

| Decision | Eleccion |
|---|---|
| Proveedor | **Local**: HuggingFace (`all-MiniLM-L6-v2`) + LM Studio. El README que documenta OpenAI es el que esta desactualizado, no el codigo. |
| Destino del proyecto | **Portfolio / demo**: justifica CI, cobertura y README impecable. |
| Estrategia de ramas | Fusionar en `master` y seguir desde ahi. |
| `--include-code` | **Eliminar** la funcionalidad (H9), no arreglarla. Es la causa de H1 y el paquete ya se describe como «RAG sobre PDFs». |
| H2 (mypy) | Subir `python_version` a `"3.12"` en `[tool.mypy]`, no fijar la version de numpy. |

---

## 4. Lo que ya esta verificado (no repetir)

Comprobado ejecutando, con Milvus 2.5.11 en Docker:

- Extraccion de PDF, chunking, embeddings, insercion en Milvus y recuperacion: **funcionan**.
- Reingesta idempotente: reindexar el mismo PDF deja el recuento en 1, no duplica.
- `pytest`: **12 tests pasan** (~33 s).
- `ruff check .`: limpio.
- `mypy src`: **falla** (H2). Con `--python-version 3.13` pasa sin errores.

**Sin verificar todavia:** la generacion de respuesta con el LLM. LM Studio no estaba escuchando
en `:1234` en esta maquina. Es lo unico del pipeline que sigue sin comprobarse de extremo a
extremo; conviene hacerlo en cuanto la maquina nueva tenga LM Studio disponible.

---

## 5. Reproduccion del fallo critico (H1)

Con un PDF ya indexado, anadir un fichero de codigo al mismo directorio y reingestar:

```bash
questbook ingest-pdf <dir_con_pdf_y_py> --include-code
```

Resultado: `DataNotMatchException: Insert missed an field 'book_title'`, y **la coleccion pasa
de N entidades a 0**, porque el borrado previo ya se habia ejecutado.

Comprobar el recuento antes y despues:

```bash
.venv/bin/python -c "
from pymilvus import MilvusClient
c = MilvusClient(uri='http://localhost:19530'); c.load_collection('questbook_documents')
print(c.query('questbook_documents', filter='pk >= 0', output_fields=['count(*)']))"
```

---

## 6. Aviso importante sobre dependencias (H3)

`pyproject.toml` solo usa `>=`, sin techos ni lockfile: **la maquina nueva puede resolver
versiones distintas a las verificadas aqui y comportarse de otra forma.** Estas son las
versiones exactas contra las que se hizo todo el diagnostico:

```
langchain 1.3.14          langchain-core 1.5.3       langchain-community 0.4.2
langchain-milvus 0.4.0    langchain-huggingface 1.2.2 langchain-openai 1.4.2
pymilvus 3.0.1            pydantic 2.13.4            pydantic-settings 2.15.0
sentence-transformers 5.7.0  torch 2.13.0            numpy 2.5.2
fastapi 0.141.1           streamlit 1.61.1           typer 0.27.1   pypdf 6.15.0
mypy 2.3.0                pytest 9.1.1               ruff 0.16.2
Python 3.13.5             Milvus 2.5.11 (Docker)
```

Ojo: el codigo se escribio contra langchain 0.2 y pymilvus 2.4. Que funcione con las mayores
de arriba es una casualidad afortunada, y es justo lo que la fase 1 debe blindar con un
lockfile.

Si algo se comporta distinto en la maquina nueva, comparar contra esta lista antes de buscar
el fallo en el codigo.

---

## 7. Estado del repositorio

- `master` local iba **7 commits por delante de `origin/master`** al fusionar la rama; verificar
  si ese push llego a hacerse antes de empezar.
- La rama `feature/openai-embeddings-milvus` sigue existiendo en el remoto y ya esta integrada:
  puede borrarse cuando el push de `master` este confirmado.
