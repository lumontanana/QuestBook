# QuestBook — Diagnostico y plan de finalizacion

Fecha: 2026-08-10
Base analizada: `master` tras fusionar `feature/openai-embeddings-milvus` (commit `0812c2b`).
Decisiones tomadas: proveedor **local** (HuggingFace + LM Studio), destino **portfolio/demo**.

Todo lo marcado como *verificado* se comprobo ejecutando el codigo con Milvus 2.5.11 real
en Docker y el entorno instalado desde cero.

---

## 1. Estado actual

El pipeline **funciona de extremo a extremo salvo la generacion de respuesta**:

| Etapa | Estado |
|---|---|
| Extraccion de PDF por pagina | Funciona (verificado) |
| Chunking + metadata (`chunk_id`, `chunk_index`) | Funciona (verificado) |
| Embeddings HuggingFace (`all-MiniLM-L6-v2`) | Funciona (verificado, descarga ~90 MB) |
| Insercion en Milvus | Funciona (verificado) |
| Reingesta sin duplicar | Funciona (verificado: 1 chunk sigue siendo 1) |
| Recuperacion (retriever) | Funciona (verificado) |
| Generacion de respuesta | **Sin verificar** — requiere LM Studio en `:1234` |
| `--include-code` | **Roto** (verificado, ver H1) |

Calidad actual: **12 tests pasan**, `ruff check` limpio, `mypy src` **falla** (ver H2).

La rama fusionada ya resolvio seis problemas reales que tenia `master`: reingesta idempotente,
tolerancia a PDFs corruptos, `chunk_index` por pagina, logging estructurado en uso,
manejo de errores en la API y arranque ordenado de Docker. El trabajo restante es el que sigue.

---

## 2. Hallazgos

### Bloqueantes

**H1 — Perdida de datos silenciosa en la ingesta. (verificado)**
`ingest_path` borra los chunks previos de cada `source` *antes* de insertar los nuevos, y la
insercion puede fallar. Reproduccion exacta: con `manual.pdf` ya indexado, ejecutar
`questbook ingest-pdf <dir> --include-code` sobre un directorio que ademas contiene un `.py`.
Milvus creo la coleccion con un esquema fijo (`source`, `book_title`, `page`, `chunk_index`,
`chunk_id`) a partir del primer PDF; los documentos de codigo no traen `book_title` ni `page`
y si traen `language`, asi que la insercion aborta con
`DataNotMatchException: Insert missed an field 'book_title'`.
**El borrado ya se habia ejecutado: la coleccion paso de 1 entidad a 0.**
Son dos defectos superpuestos:
- *H1a* — el par borrar/insertar no es atomico ni tiene rollback.
- *H1b* — la metadata es heterogenea contra un esquema de coleccion fijo.

**H2 — `mypy src` falla en instalacion limpia. (verificado)**
`python_version = "3.10"` en `pyproject.toml` choca con los stubs de numpy, que usan sintaxis
de 3.12+: `Type statement is only supported in Python 3.12 and greater`. El chequeo aborta sin
llegar a analizar el proyecto. Con `--python-version 3.13` pasa sin errores. Esto deja rojo el
comando documentado en el README, `make check` y cualquier CI futura desde el minuto cero.

**H3 — Dependencias sin techo y sin lockfile. (verificado)**
Todas las dependencias usan solo `>=`. Una instalacion limpia hoy trae **langchain 1.3.14**
(el codigo se escribio contra 0.2), **pymilvus 3.0.1** (contra 2.4), mypy 2.3, pytest 9 y
pydantic 2.13. Hoy funciona por casualidad; el proyecto no es reproducible y puede romperse
sin tocar una linea. Para un proyecto de portfolio esto es especialmente visible.

### Importantes

**H4 — Traceback alarmante en la primera ingesta. (verificado)**
`delete_by_source` se invoca contra una coleccion que aun no existe y Milvus responde
`collection not found`. `langchain_milvus` captura la excepcion internamente, asi que la
ingesta continua y termina bien, pero la consola escupe un traceback completo de pymilvus.
La primera ejecucion de un usuario nuevo parece un fallo grave sin serlo.

**H5 — Sin manejo de errores fuera de la API. (verificado)**
`questbook ask` sin LM Studio levantado muere con `APIConnectionError` y un traceback de la
libreria de OpenAI. Lo mismo ocurriria con Milvus caido. Fuera de `api/main.py` no hay ni un
`try`/`except` en `qa.py`, `providers.py` ni `vectorstore.py`.

**H6 — README desalineado con el codigo.**
Documenta OpenAI (`text-embedding-3-large`) como camino principal cuando los defaults son
HuggingFace + LM Studio; los ejemplos son solo PowerShell; no menciona el Makefile ni el
requisito de tener LM Studio corriendo.

**H7 — `docker compose up` falla en un clon limpio.**
Los servicios `api` y `streamlit` declaran `env_file: .env`, y `.env` esta en `.gitignore`.
Quien clone el repositorio y siga el README obtiene un error antes de arrancar nada.

**H8 — Sin integracion continua.**
No hay `.github/workflows`. Para un proyecto de portfolio, el badge verde y la garantia de que
los 12 tests corren en cada push es de los elementos de mayor retorno.

**H9 — `--include-code` es una funcionalidad a medias.**
Tras eliminar `code_parser.py`, el codigo se indexa como texto plano con el mismo splitter que
la prosa. Ademas rompe (H1). La descripcion del paquete ya dice "RAG sobre PDFs".
**Recomendacion: eliminar la opcion** (`CODE_SUFFIXES`, `load_text_or_code`, el flag en CLI y
API) en lugar de arreglarla, y reintroducirla mas adelante como funcionalidad propia si interesa.

### Menores

- **H10** — `tests/test_settings.py` instancia `Settings()`, que lee el `.env` real del disco.
  Un `.env` con `APP_NAME` distinto tumba el test. Debe aislarse con `monkeypatch`.
- **H11** — La UI de Streamlit no expone `top_k` ni muestra puntuaciones de similitud.
- **H12** — El `Dockerfile` instala las dependencias de desarrollo en la imagen final, no hay
  `.dockerignore` y el proceso corre como root.
- **H13** — En `qa.py` la cadena LCEL es decorativa: los documentos se recuperan antes con
  `retriever.invoke` y el `RunnableParallel` los ignora. Funciona, pero no es lo que aparenta.
- **H14** — `ingest_path` devuelve `len(files)` incluyendo los ficheros que fallaron al cargar.
- **H15** — `/ingest/path` acepta cualquier ruta del sistema. La restriccion se implemento en
  `c1f4c58` y se revirtio a conciencia en `160c46d`; conviene dejar la decision documentada.
- **H16** — `clean_pdf_text` no recompone palabras partidas con guion al final de linea.
- **H17** — Los PDFs escaneados sin capa de texto se omiten en silencio, sin aviso ni OCR.

---

## 3. Plan de finalizacion

### Fase 0 — Base de trabajo *(hecho)*
- [x] Fusionar `feature/openai-embeddings-milvus` en `master` (fast-forward).
- [x] `Makefile` con instalacion, calidad, Milvus, uso, Docker y `make doctor`.
- [x] `CLAUDE.md` con la arquitectura y las trampas del proyecto.

### Fase 1 — Bloqueantes
1. **H1b**: normalizar la metadata en `splitter.py` para que todo chunk tenga siempre el mismo
   conjunto de claves (`source`, `book_title`, `page`, `chunk_index`, `chunk_id`), rellenando
   los ausentes con valores por defecto. Alternativa: `enable_dynamic_field=True` en el
   `Milvus` de `vectorstore.py`.
2. **H1a**: invertir el orden a insertar-luego-borrar, o capturar el fallo de
   `add_documents` y no dar por buena la ingesta. Test de regresion que simule un fallo de
   insercion y verifique que los chunks previos siguen ahi.
3. **H2**: subir `python_version` a `"3.12"` en `[tool.mypy]` (o fijar `numpy`), y confirmar
   que `make typecheck` pasa.
4. **H3**: generar un lockfile reproducible y anadir techos de version a las dependencias
   criticas (`langchain*`, `pymilvus`, `pydantic`).

*Criterio de aceptacion: `make check` pasa en verde, y `--include-code` (si se conserva) o su
ausencia no puede destruir datos ya indexados.*

### Fase 2 — Robustez y experiencia de uso
5. **H4**: comprobar si la coleccion existe antes de llamar a `delete_by_source`.
6. **H5**: capturar los fallos de conexion a Milvus y al LLM, y traducirlos a mensajes claros
   en la CLI y en Streamlit ("LM Studio no responde en :1234").
7. **H9**: eliminar `--include-code` y su superficie asociada.
8. **H14**: contar solo los ficheros realmente procesados.
9. **H10**: aislar `test_settings.py` del `.env` del disco.

*Criterio de aceptacion: ninguna ruta de uso habitual muestra un traceback al usuario.*

### Fase 3 — Calidad visible (portfolio)
10. **H8**: workflow de GitHub Actions con `ruff`, `mypy` y `pytest` sobre 3.11 y 3.12.
11. Umbral de cobertura y badge en el README.
12. **H12**: `.dockerignore`, build multi-etapa sin dependencias de desarrollo y usuario no-root.
13. **H13**: reescribir la cadena de `qa.py` como un LCEL real, o simplificarla a codigo
    directo sin el envoltorio decorativo.

### Fase 4 — Documentacion
14. **H6**: reescribir el README alrededor del camino local real (HuggingFace + LM Studio),
    con OpenAI como alternativa; comandos en `bash` ademas de PowerShell; seccion de Makefile;
    requisito explicito de LM Studio.
15. **H7**: hacer que el arranque con Docker funcione en un clon limpio (`env_file` opcional o
    `make env` como paso previo documentado).
16. **H15**: documentar la decision sobre `/ingest/path`.

### Fase 5 — Mejoras opcionales
17. **H11**: `top_k` y puntuaciones en Streamlit.
18. **H16**: recomposicion de palabras con guion.
19. **H17**: detectar PDFs sin capa de texto y avisar; evaluar OCR.
20. Endpoint de subida de PDFs (`python-multipart` ya es dependencia).

---

## 4. Camino critico

Para tener la aplicacion **terminada y demostrable** basta con las fases 1 y 2 mas el punto 14.
Las fases 3 y 4 restantes son las que la convierten en un proyecto de portfolio presentable.
El unico requisito externo que queda por validar es LM Studio: hasta que no responda en
`:1234`, la ultima etapa del RAG sigue sin comprobarse de extremo a extremo.
