# Security Baseline v1

Baseline defensivo para revisar el estado actual de seguridad antes de release/deploy.

## Alcance (v1)

- Configuración por entorno (`dev/prod/cloud`).
- Diferenciación de endpoint cliente (`app_settings.json -> api.base_url`) vs bind host backend (`backend/.env* -> API_HOST`).
- TLS cliente API (`app_settings.json`).
- TLS backend directo (par `API_TLS_CERTFILE`/`API_TLS_KEYFILE`).
- TLS PostgreSQL (`DB_SSLMODE`).
- Secretos críticos (`API_JWT_SECRET`, `API_ADMIN_PASSWORD`).

## Ejecutar

```bash
python3 security/security_baseline.py --env dev
python3 security/security_baseline.py --env prod
python3 security/security_baseline.py --env cloud
```

Salida en JSON:

```bash
python3 security/security_baseline.py --env prod --format json
```

Guardar reporte Markdown:

```bash
python3 security/security_baseline.py --env cloud --format md --output security/security_report_cloud.md
```

## Criterio de fallo

Por defecto, el script retorna exit code `1` si encuentra hallazgos `high` o `critical`.

Para endurecer:

```bash
python3 security/security_baseline.py --env prod --fail-on medium
```

Para solo observación (sin fallar CI):

```bash
python3 security/security_baseline.py --env prod --fail-on none
```

## Hallazgos esperados en prod/cloud

- `API_URL_NOT_HTTPS`
- `API_VERIFY_TLS_DISABLED`
- `DB_SSLMODE_WEAK`
- `API_HOST_HAS_SCHEME` (configuración inválida de bind host backend)
- `JWT_SECRET_WEAK`
- `ADMIN_PASSWORD_WEAK`

## Integración recomendada

- Ejecutar en CI en cada PR:
  - `python3 security/security_baseline.py --env prod --format text`
- Ejecutar antes de despliegue cloud:
  - `python3 security/security_baseline.py --env cloud --format md --output <artifact>`
