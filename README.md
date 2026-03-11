# BJJ Vienna

![Build](https://img.shields.io/badge/build-Online-green)
![Release](https://img.shields.io/badge/release-v1.0.2-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![GitHub](https://img.shields.io/badge/github-repo-blue?logo=github)

Desktop application for BJJ academy operations with an optional FastAPI backend.

## What This Project Includes
- Desktop client (Tkinter) with modules for students, teachers, locations, sessions, attendance, reports, themes, and settings.
- Backend API (FastAPI) with JWT authentication, roles, and rate-limited login.
- PostgreSQL persistence.
- i18n support (`en`, `de-AT`).
- Export flows (CSV, PDF, XLSX).

## Architecture (Current)
- Canonical API: `backend/main.py`
- API runner: `python -m backend.run`
- Compatibility entrypoint: `python main.py` (wrapper)
- Desktop entrypoint: `python gui.py`

Desktop can call the API via `api_client.py`. Legacy direct DB path still exists in parts of the desktop stack.

## Key Paths
- `gui.py`: desktop entrypoint
- `ui/`: desktop modules
- `backend/main.py`: canonical FastAPI app
- `backend/run.py`: Uvicorn launcher
- `backend/config.py`: env loading and runtime security checks
- `scripts/bootstrap_instance.py`: bootstrap backend/client config
- `scripts/check_instance_config.py`: strict config validation
- `installer/bjjvienna.iss`: Windows installer definition
- `docs/PROD_SECURITY_CHECKLIST.md`: production checklist

## Local Development

### 1) Install dependencies
```bash
pip install -r requirements.txt
```

### 2) Configure instance
```bash
python3 scripts/bootstrap_instance.py --env dev
```

### 3) Run backend
```bash
python -m backend.run
```

### 4) Run desktop
```bash
python gui.py
```

### 5) Run tests
```bash
pytest -q
```

## Environment and Config
- Backend env source of truth: `backend/.env*` (`.env.dev`, `.env.stage`, `.env.demo`, `.env.production`).
- Desktop/client settings: `app_settings.json`.
- In production-like environments (`APP_ENV=stage|demo|production`), backend startup enforces strong JWT/admin credentials.
- Legacy aliases are still accepted: `APP_ENV=prod|cloud`.

## CI and Release
- CI: `.github/workflows/ci.yml`
  - Python 3.11 stable job
  - Python 3.14 experimental job (non-blocking)
- Release: `.github/workflows/release.yml`
  - quality gate (`ruff` + `pytest`)
  - build artifact and publish GitHub release on `v*` tags

## Security
- Production and cybersecurity checklist:
  - `docs/PROD_SECURITY_CHECKLIST.md`

## Recent Updates
- Attendance Week now supports filtering by active location and shows selected location in the calendar header.
- Session scheduling uniqueness is location-aware:
  - same class/date/start time is allowed across different locations.
  - same class/date/start time in the same location returns `409 Conflict`.
- Added public web pre-registration flow:
  - Static registration site under `Static/` (EN/DE switch, mobile-first improvements, dark theme, social/footer blocks).
  - Backend intake endpoint `POST /public/pre-registrations`.
  - Staff review/import endpoints `GET /pre-registrations/pending` and `POST /pre-registrations/import`.
  - Students tab statistics now includes a pre-registrations category.

## Lessons Learned (2026-03-11)
- Railway static services with Nginx must listen on `${PORT}` (otherwise `502`).
- With Docker build context at repo root, copy paths in `Static/Dockerfile` must use `Static/...`.
- Local Postgres commonly needs `DB_SSLMODE=prefer` (or `disable`) when server does not support SSL.
- `date` values in Pydantic payloads must be JSON-serialized using `model_dump(mode=\"json\")`.
- `API_CORS_ALLOW_ORIGINS` must include the deployed static domain for browser form submissions.

## Star History
<a href="https://www.star-history.com/#lkccomander/bjjvienna.git&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=lkccomander/bjjvienna.git&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=lkccomander/bjjvienna.git&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=lkccomander/bjjvienna.git&type=date&legend=top-left" />
 </picture>
</a>
