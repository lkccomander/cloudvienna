# Backend API (Step 1)

This is the first backend scaffold to remove direct DB access from the GUI client.

## Endpoints

- `GET /health`
- `POST /auth/login`
- `GET /users/list` (admin)
- `POST /users/create` (admin)
- `GET /students/list`
- `GET /students/count`
- `GET /students/{id}`
- `POST /students/create`
- `PUT /students/{id}`
- `POST /students/{id}/deactivate`
- `POST /students/{id}/reactivate`
- `GET /locations/active`
- `GET /locations/list`
- `POST /locations/create`
- `PUT /locations/{id}`
- `POST /locations/{id}/deactivate`
- `POST /locations/{id}/reactivate`
- `GET /teachers/list`
- `GET /teachers/active`
- `POST /teachers/create`
- `PUT /teachers/{id}`
- `POST /teachers/{id}/deactivate`
- `POST /teachers/{id}/reactivate`
- `GET /classes/list`
- `GET /classes/active`
- `POST /classes/create`
- `PUT /classes/{id}`
- `POST /classes/{id}/deactivate`
- `POST /classes/{id}/reactivate`
- `GET /sessions/list`
- `POST /sessions/create`
- `PUT /sessions/{id}`
- `POST /sessions/{id}/cancel`
- `POST /sessions/{id}/restore`
- `POST /attendance/register`
- `GET /attendance/by-session/{id}`
- `GET /attendance/by-student/{id}`
- `POST /reports/students/search`
- `POST /reports/students/export`

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
- `API_HOST` (optional, default: `127.0.0.1`)
- `API_PORT` (optional, default: `8000`)
- `API_PROXY_HEADERS` (optional, default: `true`)
- `API_TLS_CERTFILE` (optional, requires `API_TLS_KEYFILE`)
- `API_TLS_KEYFILE` (optional, requires `API_TLS_CERTFILE`)

## Run

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Recommended (uses `backend/.env`):

```bash
python -m backend.run
```

To enable direct HTTPS on Uvicorn, set both `API_TLS_CERTFILE` and `API_TLS_KEYFILE`, then run:

```bash
python -m backend.run
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

## GUI -> API config

Add this block to your `app_settings.json` so the Students tab can use the API:

```json
{
  "api": {
    "base_url": "https://127.0.0.1:8000",
    "username": "admin",
    "password": "change-me",
    "verify_tls": true,
    "ca_file": "C:/path/to/ca-or-selfsigned-cert.pem"
  }
}
```

Notes:
- Keep `verify_tls: true` in production.
- For local self-signed certificates, either trust the cert in OS trust store or set `ca_file`.
- Use `verify_tls: false` only for temporary local development.
- On first startup, the API bootstraps an admin user into `t_api_users` from
  `API_ADMIN_USER` and `API_ADMIN_PASSWORD` if that username does not exist yet.
