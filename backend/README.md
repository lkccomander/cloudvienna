# Backend API (Step 1)

This is the first backend scaffold to remove direct DB access from the GUI client.

## Endpoints

- `GET /health`
- `POST /auth/login`
- `GET /students/list`
- `POST /students/create`

## Environment variables

Set these before running:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_SSLMODE` (optional, default: `prefer`)
- `API_ADMIN_USER` (default: `admin`)
- `API_ADMIN_PASSWORD` (default: `change-me`)
- `API_JWT_SECRET` (required in production)
- `API_TOKEN_MINUTES` (optional, default: `60`)

## Run

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

## Quick test

```bash
curl -s http://127.0.0.1:8000/health
```

```bash
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"change-me"}'
```

