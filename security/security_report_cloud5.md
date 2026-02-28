# Security Baseline Report

- Environment: `cloud`
- Status: `fail`
- Findings: `1`

## Context
- Backend API host: `https://backend-unique-tenderness-stage.up.railway.app`
- API base URL: `https://backend-unique-tenderness-stage.up.railway.app`
- API verify TLS: `True`
- DB SSL mode: `require`
- Env files: `C:\Projects\cloudvienna\backend\.env.cloud`

## Findings
- **MEDIUM** `API_HOST_HAS_SCHEME`: API_HOST includes URL scheme
  - Current API_HOST='https://backend-unique-tenderness-stage.up.railway.app'. Use a bind host/IP only (e.g., 0.0.0.0 or 127.0.0.1); keep URLs in app_settings.json api.base_url.
