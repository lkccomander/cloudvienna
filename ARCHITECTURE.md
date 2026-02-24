# Architecture

## Overview
- BJJ Vienna is a desktop application built with Tkinter. The main window is a tabbed UI
  composed of feature modules under `ui/`.
- Data is stored in PostgreSQL.
- API backend implementation is centralized in `backend/main.py`.
- Root `main.py` is a compatibility wrapper that forwards to `backend.run`.
- UI text is localized via JSON files under `i18n/`, with language selection persisted in
  `app_settings.json`.

## High-level flow
1. `gui.py` boots the Tkinter app, builds tabs, and wires up each module's `build(...)`.
2. `ui/*.py` modules call API through `api_client.py` (JWT login + Bearer requests).
3. Backend (`backend/main.py`) applies auth/roles and executes DB queries via `backend/db.py`.
4. Legacy direct DB path (`db.py`) still exists in parts of the desktop stack for compatibility.
5. Results are rendered in Tk widgets such as `Treeview`, charts, and forms.

## Key modules
- `gui.py`: App entry point and Tk notebook/tab wiring.
- `ui/`: Feature tabs (students, teachers, locations, sessions, attendance, reports, settings, about).
- `api_client.py`: Desktop API client, token lifecycle, and authenticated requests.
- `db.py`: Legacy direct DB helper path (kept for compatibility).
- `version.py`: App version string used in the window title.
- `backend/main.py`: Canonical FastAPI app.
- `backend/run.py`: Uvicorn launcher for API.
- `backend/config.py`: Env/config loading and security validation.
- `main.py`: compatibility entrypoint for `python main.py`.
- `scripts/bootstrap_instance.py`: bootstrap backend env + desktop settings.
- `scripts/check_instance_config.py`: strict config validation gate.
- `i18n.py`: Loads translations and persists language choice.

## Data access
- Backend data access uses `backend/db.py` with a PostgreSQL pool.
- Backend env source of truth is `backend/.env*` (`.env.dev/.env.prod/.env.cloud`).
- Desktop direct DB access via `db.py` is legacy-compatible but no longer the target architecture.

## DB schema summary (inferred from UI queries)
- `t_locations`: `id`, `name` (unique), `phone`, `address`, `active`, `created_at`, `updated_at`.
- `t_students`: `id`, `name`, `sex`, `direction`, `postalcode`, `belt`, `email`, `phone`, `phone2`,
  `weight`, `country`, `taxid`, `birthday`, `location_id` (FK to `t_locations`), `active`,
  `newsletter_opt_in`, `updated_at`.
- `public.t_coaches`: `id`, `name`, `sex`, `email`, `phone`, `belt`, `hire_date`, `active`, `updated_at`.
- `t_classes`: `id`, `name`, `belt_level`, `coach_id` (FK to `public.t_coaches`), `duration_min`, `active`.
- `t_class_sessions`: `id`, `class_id` (FK to `t_classes`), `session_date`, `start_time`, `end_time`,
  `location_id` (FK to `t_locations`), `cancelled`.
- `t_attendance`: `session_id` (FK to `t_class_sessions`), `student_id` (FK to `t_students`),
  `status`, `checkin_source`, `checkin_time`.

## Reports and exports
- Reports search supports name, location, newsletter consent, and active/inactive filters with pagination.
- Export supports CSV/PDF/Excel to the project root. PDF uses `reportlab`; Excel uses `openpyxl`.

## Configuration
- Backend: `backend/.env*` controls DB/API runtime values (`APP_ENV` selects variant).
- Desktop: `app_settings.json` stores API endpoint/credentials and user preferences.
- `scripts/bootstrap_instance.py` writes both backend env and client settings for first-time setup.
- In `prod/cloud`, backend startup fails fast when critical secrets are weak/default.

## Logging
- `gui.py` configures error logging to `app.log` and the console.
- About/Config includes a manual log viewer that reads `app.log`.

## Build and distribution
- `requirements.txt` lists runtime and tooling dependencies.
- `pyinstaller` is used for packaging (see `gui.spec`).
- Installer is defined in `installer/bjjvienna.iss` (first-run settings page support).
- CI: `.github/workflows/ci.yml` (Python 3.11 stable + 3.14 experimental).
- Release: `.github/workflows/release.yml` includes quality gate (`ruff` + `pytest`) before publishing.

## Security highlights
- JWT auth, role checks, and login rate-limiting are implemented in `backend/main.py`.
- Production checklist lives in `docs/PROD_SECURITY_CHECKLIST.md`.
