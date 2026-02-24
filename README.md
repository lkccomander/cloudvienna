# BJJ Vienna

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
- Backend env source of truth: `backend/.env*` (`.env.dev`, `.env.prod`, `.env.cloud`).
- Desktop/client settings: `app_settings.json`.
- In production-like environments (`APP_ENV=prod|cloud`), backend startup enforces strong JWT/admin credentials.

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

## Star History
<a href="https://www.star-history.com/#lkccomander/bjjvienna.git&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=lkccomander/bjjvienna.git&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=lkccomander/bjjvienna.git&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=lkccomander/bjjvienna.git&type=date&legend=top-left" />
 </picture>
</a>
