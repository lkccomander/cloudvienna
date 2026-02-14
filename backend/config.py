import json
import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
APP_SETTINGS_PATH = ROOT_DIR / "app_settings.json"

# Backend-specific env files have priority for API credentials/settings.
# Root-level env files are kept as fallback for compatibility.
load_dotenv(BACKEND_DIR / ".env", override=False)
load_dotenv(BACKEND_DIR / ".env.dev", override=False)
load_dotenv(ROOT_DIR / ".env", override=False)
load_dotenv(ROOT_DIR / ".env.dev", override=False)


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

API_ADMIN_USER = os.getenv("API_ADMIN_USER", "admin")
API_ADMIN_PASSWORD = os.getenv("API_ADMIN_PASSWORD", "change-me")
