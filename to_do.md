# TO DO

- [ ] Implementar ofuscación del cliente desktop antes del empaquetado (`PyArmor`).
- [ ] Empaquetar ejecutable final (`PyInstaller`) usando la salida ofuscada.
- [ ] Firmar `CloudVienna.exe` con certificado de código (`signtool` + timestamp).
- [ ] Verificar firma del binario (`signtool verify /pa /v`).
- [ ] Documentar el proceso en un script de build reproducible (`build.ps1`).
- [ ] Confirmar que no haya secretos hardcodeados en el cliente (mover lógica/secretos críticos al backend).

## Nota

La ofuscación y la firma no eliminan la ingeniería inversa; solo la dificultan y mejoran confianza/integridad del ejecutable.

## Separar backend del instalador

- [ ] Ajustar `gui.spec` para no incluir `backend/` ni dependencias de FastAPI en el `.exe`.
- [ ] Dejar el instalador con solo cliente desktop (`gui.py`, `ui/`, `api_client.py`, `i18n/`, assets).
- [ ] Confirmar que la app desktop consuma únicamente API remota (sin ejecutar backend local).
- [ ] Mover validaciones/reglas críticas al backend y exponerlas por endpoints.
- [ ] Verificar que `app_settings.json` use solo `api_base_url` (HTTPS) para conectar con servidor.
- [ ] Excluir `backend/.env*` y cualquier secreto del proceso de build del instalador.
- [ ] Confirmar que PostgreSQL solo acepte conexiones desde backend (no desde clientes desktop).

## Hardening TLS (API + DB)

- [ ] En `prod/cloud`, bloquear `api.base_url` con `http://` y exigir `https://` en validaciones de arranque (`scripts/check_instance_config.py` + backend).
- [ ] En `prod/cloud`, bloquear `api.verify_tls=false` y exigir verificación TLS activa en cliente.
- [ ] Exigir `DB_SSLMODE=require` o idealmente `verify-full` en `prod/cloud` (evitar `prefer`).
- [ ] Agregar checks TLS explícitos en `scripts/check_instance_config.py` para fallar rápido si hay configuración insegura.
- [ ] Corregir defaults de instalador no-Railway para evitar que se propague config insegura (`http://127.0.0.1:8000` + `verify_tls=false`).
- [ ] Definir estrategia TLS del backend: terminar TLS en proxy (Railway/Nginx) o usar `API_TLS_CERTFILE` + `API_TLS_KEYFILE` si se expone directo.
