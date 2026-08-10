# QuestBook -- automatizacion de instalacion, calidad y puesta en marcha.
# Ejecuta `make` o `make help` para ver todos los objetivos disponibles.

.DEFAULT_GOAL := help
SHELL := /bin/bash

# --- Colores -----------------------------------------------------------------
C_RESET := \033[0m
C_BOLD  := \033[1m
C_DIM   := \033[2m
C_BLUE  := \033[36m
C_GREEN := \033[32m
C_YELL  := \033[33m
C_RED   := \033[31m
C_MAG   := \033[35m

# --- Rutas y binarios --------------------------------------------------------
VENV    := .venv
PY      := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
PYTEST  := $(VENV)/bin/pytest
RUFF    := $(VENV)/bin/ruff
MYPY    := $(VENV)/bin/mypy
QB      := $(VENV)/bin/questbook
STAMP   := $(VENV)/.install-stamp

# --- Parametros configurables ------------------------------------------------
PDF_DIR   ?= data/raw
Q         ?= De que trata el libro?
API_PORT  ?= 8000
UI_PORT   ?= 8501
MILVUS_URL ?= http://localhost:9091/healthz

define banner
	@printf "$(C_MAG)$(C_BOLD)\n"; \
	printf "   ___                 _   ____              _   \n"; \
	printf "  / _ \\ _   _  ___ ___| |_| __ )  ___   ___ | | __\n"; \
	printf " | | | | | | |/ _ \\ __| __|  _ \\ / _ \\ / _ \\| |/ /\n"; \
	printf " | |_| | |_| |  __\\__ \\ |_| |_) | (_) | (_) |   < \n"; \
	printf "  \\__\\_\\\\__,_|\\___|___/\\__|____/ \\___/ \\___/|_|\\_\\\\\n"; \
	printf "$(C_RESET)$(C_DIM)          RAG sobre tu biblioteca de PDFs$(C_RESET)\n\n"
endef

# =============================================================================
help: ## Muestra esta ayuda
	$(banner)
	@printf "$(C_BOLD)Uso:$(C_RESET) make $(C_BLUE)<objetivo>$(C_RESET)\n\n"
	@awk 'BEGIN {FS = ":.*?## "} \
		/^# =+$$/ {next} \
		/^##@/ {printf "\n$(C_BOLD)%s$(C_RESET)\n", substr($$0, 5); next} \
		/^[a-zA-Z_-]+:.*?## / {printf "  $(C_BLUE)%-18s$(C_RESET) %s\n", $$1, $$2}' \
		$(MAKEFILE_LIST)
	@printf "\n$(C_DIM)Variables: PDF_DIR=$(PDF_DIR)  API_PORT=$(API_PORT)  UI_PORT=$(UI_PORT)$(C_RESET)\n"
	@printf "$(C_DIM)Ejemplo:   make ask Q=\"Cual es la idea principal?\"$(C_RESET)\n\n"

##@ Instalacion

$(VENV):
	@printf "$(C_BLUE)==>$(C_RESET) Creando entorno virtual en $(VENV)...\n"
	@python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip --quiet

$(STAMP): $(VENV) pyproject.toml
	@printf "$(C_BLUE)==>$(C_RESET) Instalando QuestBook y dependencias (puede tardar varios minutos)...\n"
	@$(PIP) install -e ".[dev]"
	@touch $(STAMP)
	@printf "$(C_GREEN)OK$(C_RESET) Entorno listo.\n"

install: $(STAMP) ## Crea el venv e instala el proyecto con dependencias de desarrollo

env: ## Crea el fichero .env a partir de .env.example (no sobrescribe)
	@if [ -f .env ]; then \
		printf "$(C_YELL)!!$(C_RESET)  .env ya existe, no se toca.\n"; \
	else \
		cp .env.example .env; \
		printf "$(C_GREEN)OK$(C_RESET) .env creado desde .env.example. Revisa la configuracion.\n"; \
	fi

setup: install env ## Instalacion completa: venv + dependencias + .env
	@printf "\n$(C_GREEN)$(C_BOLD)QuestBook instalado.$(C_RESET)\n"
	@printf "   Siguiente paso: $(C_BLUE)make milvus-up$(C_RESET) y luego $(C_BLUE)make ingest$(C_RESET)\n\n"

##@ Calidad

test: $(STAMP) ## Ejecuta la bateria de tests
	@$(PYTEST)

test-cov: $(STAMP) ## Tests con informe de cobertura
	@$(PYTEST) --cov=questbook --cov-report=term-missing --cov-report=html
	@printf "$(C_GREEN)OK$(C_RESET) Informe HTML en htmlcov/index.html\n"

lint: $(STAMP) ## Comprueba el estilo con ruff
	@$(RUFF) check .

format: $(STAMP) ## Corrige estilo e imports automaticamente
	@$(RUFF) check --fix .
	@$(RUFF) format .

typecheck: $(STAMP) ## Comprueba tipos con mypy en modo strict
	@$(MYPY) src

check: lint typecheck test ## Lint + tipos + tests (lo que deberia pasar antes de un commit)
	@printf "\n$(C_GREEN)$(C_BOLD)Todas las comprobaciones han pasado.$(C_RESET)\n\n"

##@ Milvus

milvus-up: ## Levanta Milvus en Docker y espera a que este sano
	@printf "$(C_BLUE)==>$(C_RESET) Levantando Milvus...\n"
	@docker compose up -d milvus
	@printf "$(C_BLUE)==>$(C_RESET) Esperando healthcheck"
	@for i in $$(seq 1 60); do \
		if curl -sf $(MILVUS_URL) > /dev/null 2>&1; then \
			printf "\n$(C_GREEN)OK$(C_RESET) Milvus disponible en http://localhost:19530\n"; \
			exit 0; \
		fi; \
		printf "."; sleep 3; \
	done; \
	printf "\n$(C_RED)ERROR$(C_RESET) Milvus no respondio a tiempo. Revisa: make milvus-logs\n"; \
	exit 1

milvus-down: ## Detiene Milvus (conserva los datos en ./volumes)
	@docker compose stop milvus
	@printf "$(C_GREEN)OK$(C_RESET) Milvus detenido. Los datos siguen en ./volumes/milvus\n"

milvus-logs: ## Muestra los logs de Milvus en vivo
	@docker compose logs -f milvus

milvus-reset: ## ATENCION: borra el contenedor y TODOS los vectores indexados
	@printf "$(C_RED)$(C_BOLD)Esto borrara todos los datos indexados en Milvus.$(C_RESET)\n"
	@read -p "Escribe 'si' para confirmar: " ans; \
	if [ "$$ans" = "si" ]; then \
		docker compose rm -sf milvus && rm -rf volumes/milvus; \
		printf "$(C_GREEN)OK$(C_RESET) Milvus reiniciado desde cero.\n"; \
	else \
		printf "$(C_YELL)!!$(C_RESET)  Cancelado.\n"; \
	fi

##@ Uso

ingest: $(STAMP) ## Indexa los PDFs de PDF_DIR (por defecto data/raw)
	@printf "$(C_BLUE)==>$(C_RESET) Indexando $(PDF_DIR)...\n"
	@$(QB) ingest-pdf $(PDF_DIR)

ask: $(STAMP) ## Pregunta desde la CLI. Uso: make ask Q="tu pregunta"
	@$(QB) ask "$(Q)"

api: $(STAMP) ## Arranca la API FastAPI en modo recarga automatica
	@printf "$(C_BLUE)==>$(C_RESET) API en http://localhost:$(API_PORT)/docs\n"
	@$(VENV)/bin/uvicorn questbook.api.main:app --reload --port $(API_PORT)

ui: $(STAMP) ## Arranca la interfaz Streamlit
	@printf "$(C_BLUE)==>$(C_RESET) Streamlit en http://localhost:$(UI_PORT)\n"
	@$(VENV)/bin/streamlit run apps/streamlit_app.py --server.port $(UI_PORT)

##@ Docker

up: ## Levanta la pila completa (Milvus + API + Streamlit)
	@docker compose up -d --build
	@printf "$(C_GREEN)OK$(C_RESET) Milvus:19530  API:$(API_PORT)  Streamlit:$(UI_PORT)\n"

down: ## Detiene la pila completa
	@docker compose down

logs: ## Logs de todos los servicios en vivo
	@docker compose logs -f

##@ Mantenimiento

doctor: ## Diagnostica el entorno: venv, .env, Milvus y LLM local
	$(banner)
	@printf "$(C_BOLD)Diagnostico del entorno$(C_RESET)\n\n"
	@if [ -x $(PY) ]; then \
		printf "  $(C_GREEN)OK$(C_RESET)    venv        $$($(PY) --version 2>&1)\n"; \
	else \
		printf "  $(C_RED)FALTA$(C_RESET) venv        ejecuta: make install\n"; fi
	@if [ -f $(STAMP) ]; then \
		printf "  $(C_GREEN)OK$(C_RESET)    paquete     questbook instalado en modo editable\n"; \
	else \
		printf "  $(C_RED)FALTA$(C_RESET) paquete     ejecuta: make install\n"; fi
	@if [ -f .env ]; then \
		printf "  $(C_GREEN)OK$(C_RESET)    .env        presente\n"; \
	else \
		printf "  $(C_RED)FALTA$(C_RESET) .env        ejecuta: make env\n"; fi
	@if curl -sf $(MILVUS_URL) > /dev/null 2>&1; then \
		printf "  $(C_GREEN)OK$(C_RESET)    Milvus      respondiendo en localhost:19530\n"; \
	else \
		printf "  $(C_RED)CAIDO$(C_RESET) Milvus      ejecuta: make milvus-up\n"; fi
	@if curl -sf http://localhost:1234/v1/models > /dev/null 2>&1; then \
		printf "  $(C_GREEN)OK$(C_RESET)    LLM local   LM Studio respondiendo en :1234\n"; \
	else \
		printf "  $(C_YELL)AVISO$(C_RESET) LLM local   LM Studio no responde en :1234 (necesario para preguntar)\n"; fi
	@printf "  $(C_DIM)PDFs        $$(ls -1 $(PDF_DIR)/*.pdf 2>/dev/null | wc -l | tr -d ' ') fichero(s) en $(PDF_DIR)$(C_RESET)\n\n"

clean: ## Borra cachés, artefactos de build y cobertura
	@rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage build dist
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name '*.egg-info' -prune -exec rm -rf {} + 2>/dev/null || true
	@printf "$(C_GREEN)OK$(C_RESET) Caches eliminadas.\n"

clean-all: clean ## Borra ademas el entorno virtual
	@rm -rf $(VENV)
	@printf "$(C_GREEN)OK$(C_RESET) Entorno virtual eliminado.\n"

.PHONY: help install env setup test test-cov lint format typecheck check \
        milvus-up milvus-down milvus-logs milvus-reset \
        ingest ask api ui up down logs doctor clean clean-all
