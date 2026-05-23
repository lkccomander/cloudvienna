# AGENTS.md

Guía para agentes que trabajen en este repositorio.

## Objetivo del proyecto
- Aplicación de escritorio para gestión de academia BJJ (Tkinter + PostgreSQL).
- API FastAPI para autenticación y operaciones de backend.

## Puntos de entrada
- Desktop: `gui.py`
- API: `backend/main.py` (canónico). `main.py` es wrapper de compatibilidad.
- Acceso a datos: `db.py`
- UI modular: `ui/*.py`

## Comandos útiles
- Instalar dependencias: `pip install -r requirements.txt`
- Ejecutar app desktop: `python gui.py`
- Ejecutar API: `python -m backend.run` (recomendado) o `python main.py` (compatibilidad)
- Ejecutar tests: `pytest -q`

## Reglas de trabajo
- Hacer cambios pequeños y enfocados.
- No mezclar refactors amplios con fixes funcionales en el mismo cambio.
- Mantener compatibilidad de comportamiento existente salvo instrucción explícita.
- No introducir secretos en código o commits.

## Base de datos y configuración
- Config del cliente desktop en `app_settings.json`.
- Config del backend en `backend/.env*` (`backend/.env.dev`, `backend/.env.prod`, `backend/.env.cloud`).
- `APP_ENV` selecciona el archivo de entorno backend a usar.
- Mantener el patrón actual de carga de credenciales (env/keyring); no hardcodear secretos.

## i18n
- Archivos de idioma: `i18n/en.json` y `i18n/de-AT.json`.
- Si se agrega texto UI nuevo, actualizar ambos archivos de traducción.

## Validación mínima antes de terminar
- Ejecutar `pytest -q` si el cambio toca lógica validable.
- Si cambia configuración/arranque backend, ejecutar:
  - `python3 scripts/check_instance_config.py --env dev` (o `prod/cloud` según el caso)
- Si cambia UI, revisar que `gui.py` levante sin errores.
- Si cambia reportes/exportación, validar flujo CSV/PDF/Excel.

## Referencias internas
- Arquitectura: `ARCHITECTURE.md`
- Contexto para LLMs: `llms.txt`
- Skills disponibles en esta sesión: `SKILLS.md`

<!-- context7 -->
Use Context7 MCP to fetch current documentation whenever the user asks about a library, framework, SDK, API, CLI tool, or cloud service -- even well-known ones like React, Next.js, Prisma, Express, Tailwind, Django, or Spring Boot. This includes API syntax, configuration, version migration, library-specific debugging, setup instructions, and CLI tool usage. Use even when you think you know the answer -- your training data may not reflect recent changes. Prefer this over web search for library docs.

Do not use for: refactoring, writing scripts from scratch, debugging business logic, code review, or general programming concepts.

## Steps

1. Always start with `resolve-library-id` using the library name and the user's question, unless the user provides an exact library ID in `/org/project` format
2. Pick the best match (ID format: `/org/project`) by: exact name match, description relevance, code snippet count, source reputation (High/Medium preferred), and benchmark score (higher is better). If results don't look right, try alternate names or queries (e.g., "next.js" not "nextjs", or rephrase the question). Use version-specific IDs when the user mentions a version
3. `query-docs` with the selected library ID and the user's full question (not single words)
4. Answer using the fetched docs
<!-- context7 -->
