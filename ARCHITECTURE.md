# Architecture

## Overview
- BJJ Vienna is a desktop application built with Tkinter. The main window is a tabbed UI
  composed of feature modules under `ui/`.
- Data is stored in a PostgreSQL database and accessed through `db.py` using `psycopg2`.
- There is a small FastAPI service in `main.py` for attendance-related endpoints
  (likely optional or experimental).

## High-level flow
1. `gui.py` boots the Tkinter app, builds tabs, and wires up each module's `build(...)`.
2. Each `ui/*.py` module defines UI widgets and calls `db.execute(...)` for data access.
3. Results are rendered in Tk widgets such as `Treeview`, charts, and forms.

## Key modules
- `gui.py`: App entry point and Tk notebook/tab wiring.
- `ui/`: Feature tabs (students, teachers, locations, sessions, attendance, reports, settings, about).
- `db.py`: Database connection and query execution via `execute(...)`.
- `version.py`: App version string used in the window title.
- `main.py`: FastAPI app with attendance endpoints (if run separately).

## Data access
- `db.py` loads environment variables from `.env` (or `.env.dev/.env.prod/.env.cloud`
  based on `APP_ENV`) and opens a single shared PostgreSQL connection.
- `execute(query, params=None)` runs SQL and returns `fetchall()` results when applicable.

## DB schema summary (inferred from UI queries)
- `t_locations`: `id`, `name` (unique), `phone`, `address`, `active`, `created_at`, `updated_at`.
- `t_students`: `id`, `name`, `sex`, `direction`, `postalcode`, `belt`, `email`, `phone`, `phone2`,
  `weight`, `country`, `taxid`, `birthday`, `location_id` (FK to `t_locations`), `active`, `updated_at`.
- `public.t_coaches`: `id`, `name`, `sex`, `email`, `phone`, `belt`, `hire_date`, `active`, `updated_at`.
- `t_classes`: `id`, `name`, `belt_level`, `coach_id` (FK to `public.t_coaches`), `duration_min`, `active`.
- `t_class_sessions`: `id`, `class_id` (FK to `t_classes`), `session_date`, `start_time`, `end_time`,
  `location_id` (FK to `t_locations`), `cancelled`.
- `t_attendance`: `session_id` (FK to `t_class_sessions`), `student_id` (FK to `t_students`),
  `status`, `checkin_source`, `checkin_time`.

## Configuration
- Database credentials are provided via environment variables in `.env*` files.
- Environment selection is controlled by `APP_ENV`.

## Logging
- `gui.py` configures error logging to `app.log` for startup failures and runtime errors.

## Build and distribution
- `requirements.txt` lists runtime and tooling dependencies.
- `pyinstaller` is used for packaging (see `gui.spec`).
- GitHub Actions workflow is defined in `.github/workflows/release.yml` for releases.
