# Security Baseline Report

- Environment: `cloud`
- Status: `fail`
- Findings: `3`

## Context
- Backend API host: `https://backend-unique-tenderness-stage.up.railway.app`
- API base URL: `https://backend-unique-tenderness-stage.up.railway.app`
- API verify TLS: `False`
- DB SSL mode: `prefer`
- Env files: `C:\Projects\cloudvienna\backend\.env.cloud`

## Findings
- **CRITICAL** `API_VERIFY_TLS_DISABLED`: TLS verification disabled in prod/cloud
  - Set app_settings.json api.verify_tls=true and use trusted certificates or ca_file.
- **HIGH** `DB_SSLMODE_WEAK`: DB SSL mode is weak in prod/cloud
  - Current DB_SSLMODE='prefer'. Recommended: require, verify-ca, or verify-full.
- **MEDIUM** `API_HOST_HAS_SCHEME`: API_HOST includes URL scheme
  - Current API_HOST='https://backend-unique-tenderness-stage.up.railway.app'. Use a bind host/IP only (e.g., 0.0.0.0 or 127.0.0.1); keep URLs in app_settings.json api.base_url.
