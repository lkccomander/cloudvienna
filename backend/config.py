import json
import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
APP_SETTINGS_PATH = ROOT_DIR / "app_settings.json"
APP_ENV = os.getenv("APP_ENV", "dev").strip().lower()

# Backend uses backend-scoped env files as single source of truth.
_env_variant = {
    "dev": ".env.dev",
    "prod": ".env.prod",
    "cloud": ".env.cloud",
}.get(APP_ENV, ".env")
ENV_FILE_PRIORITY = [
    BACKEND_DIR / ".env",
    BACKEND_DIR / _env_variant,
]
for env_file in ENV_FILE_PRIORITY:
    # API runs in project-scoped mode: env files should override machine/user env vars.
    load_dotenv(env_file, override=True)
ENV_FILES_PRESENT = [str(path) for path in ENV_FILE_PRIORITY if path.exists()]


def _load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _get_db_settings() -> dict:
    return _load_json(APP_SETTINGS_PATH).get("db", {})


_db = _get_db_settings()

DB_HOST = os.getenv("DB_HOST", str(_db.get("host", "localhost")))
DB_PORT = int(os.getenv("DB_PORT", _db.get("port", 5432)))
DB_NAME = os.getenv("DB_NAME", str(_db.get("name", "")))
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_SSLMODE = os.getenv("DB_SSLMODE", str(_db.get("sslmode", "prefer")))

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_TLS_CERTFILE = os.getenv("API_TLS_CERTFILE", "").strip()
API_TLS_KEYFILE = os.getenv("API_TLS_KEYFILE", "").strip()
API_PROXY_HEADERS = os.getenv("API_PROXY_HEADERS", "true").strip().lower() in {"1", "true", "yes", "on"}
API_JWT_SECRET = os.getenv("API_JWT_SECRET", "CHANGE_ME_IN_ENV")
API_JWT_ALGORITHM = "HS256"
API_TOKEN_MINUTES = int(os.getenv("API_TOKEN_MINUTES", "60"))
API_LOGIN_RATE_LIMIT_ATTEMPTS = int(os.getenv("API_LOGIN_RATE_LIMIT_ATTEMPTS", "5"))
API_LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("API_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "300"))
API_LOGIN_BLOCK_SECONDS = int(os.getenv("API_LOGIN_BLOCK_SECONDS", "900"))

API_ADMIN_USER = os.getenv("API_ADMIN_USER", "admin")
API_ADMIN_PASSWORD = os.getenv("API_ADMIN_PASSWORD", "change-me")


def validate_security_settings() -> None:
    if APP_ENV not in {"prod", "cloud"}:
        return

    if API_JWT_SECRET == "CHANGE_ME_IN_ENV" or len(API_JWT_SECRET.strip()) < 32:
        raise RuntimeError(
            "Invalid API_JWT_SECRET for production/cloud. Set a strong secret with at least 32 characters."
        )
    if API_ADMIN_PASSWORD == "change-me" or len(API_ADMIN_PASSWORD.strip()) < 12:
        raise RuntimeError(
            "Invalid API_ADMIN_PASSWORD for production/cloud. Set a non-default password with at least 12 characters."
        )
