# AGENTS.md

Guía para agentes que trabajen en este repositorio.

## Objetivo del proyecto
- Aplicación de escritorio para gestión de academia BJJ (Tkinter + PostgreSQL).
- API opcional para asistencia (FastAPI).

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
- Config local en `app_settings.json`.
- Variables de entorno en `.env`, `.env.dev`, `.env.prod`, `.env.cloud`.
- Respetar el patrón actual de carga de credenciales (env/keyring).

## i18n
- Archivos de idioma: `i18n/en.json` y `i18n/de-AT.json`.
- Si se agrega texto UI nuevo, actualizar ambos archivos de traducción.

## Validación mínima antes de terminar
- Ejecutar `pytest -q` si el cambio toca lógica validable.
- Si cambia UI, revisar que `gui.py` levante sin errores.
- Si cambia reportes/exportación, validar flujo CSV/PDF/Excel.

## Referencias internas
- Arquitectura: `ARCHITECTURE.md`
- Contexto para LLMs: `llms.txt`
- Skills disponibles en esta sesión: `SKILLS.md`
