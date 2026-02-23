# Architecture

## Overview
- BJJ Vienna is a desktop application built with Tkinter. The main window is a tabbed UI
  composed of feature modules under `ui/`.
- Data is stored in a PostgreSQL database and accessed through `db.py` using `psycopg2`.
- FastAPI backend implementation is centralized in `backend/main.py`.
- Root `main.py` is a compatibility wrapper that forwards to `backend.run`.
- UI text is localized via JSON files under `i18n/`, with language selection persisted in
  `app_settings.json`.

## High-level flow
1. `gui.py` boots the Tkinter app, builds tabs, and wires up each module's `build(...)`.
2. Each `ui/*.py` module defines UI widgets and calls `db.execute(...)` for data access.
3. Results are rendered in Tk widgets such as `Treeview`, charts, and forms.

## Key modules
- `gui.py`: App entry point and Tk notebook/tab wiring.
- `ui/`: Feature tabs (students, teachers, locations, sessions, attendance, reports, settings, about).
- `db.py`: Database connection and query execution via `execute(...)`.
- `version.py`: App version string used in the window title.
- `backend/main.py`: Canonical FastAPI app.
- `main.py`: compatibility entrypoint for `python main.py`.
- `i18n.py`: Loads translations and persists language choice.

## Data access
- `db.py` loads environment variables from `.env` (or `.env.dev/.env.prod/.env.cloud`
  based on `APP_ENV`) and opens a single shared PostgreSQL connection.
- `execute(query, params=None)` runs SQL and returns `fetchall()` results when applicable.

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
- DB connection settings (host/port/name/sslmode) live in `app_settings.json` and can be overridden by `.env*`.
- DB credentials are loaded from environment variables when present, otherwise from Windows Credential Manager via `keyring`.
- Environment selection is controlled by `APP_ENV`.
- User preferences (language and logo path) are saved to `app_settings.json`.

## Logging
- `gui.py` configures error logging to `app.log` and the console.
- About/Config includes a manual log viewer that reads `app.log`.

## Build and distribution
- `requirements.txt` lists runtime and tooling dependencies.
- `pyinstaller` is used for packaging (see `gui.spec`).
- GitHub Actions workflow is defined in `.github/workflows/release.yml` for releases.
