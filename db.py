import json
import os
import sys

import keyring
import psycopg2
import tkinter as tk
from api_client import is_api_configured
from tkinter import messagebox, simpledialog
from dotenv import load_dotenv
from psycopg2 import OperationalError

_env = os.getenv("APP_ENV", "default").lower()
_base_dir = os.path.dirname(os.path.abspath(__file__))
_dev_env = os.path.join(_base_dir, ".env.dev")
_default_env = os.path.join(_base_dir, ".env")
_prod_env = os.path.join(_base_dir, ".env.prod")
_cloud_env = os.path.join(_base_dir, ".env.cloud")
_loaded_env_path = None

if _env == "prod":
    if os.path.exists(_prod_env):
        load_dotenv(_prod_env, override=True)
        _loaded_env_path = _prod_env
    else:
        load_dotenv(_default_env, override=True)
        _loaded_env_path = _default_env
elif _env == "dev":
    if os.path.exists(_dev_env):
        load_dotenv(_dev_env, override=True)
        _loaded_env_path = _dev_env
    else:
        load_dotenv(_default_env, override=True)
        _loaded_env_path = _default_env
elif _env == "cloud":
    if os.path.exists(_cloud_env):
        load_dotenv(_cloud_env, override=True)
        _loaded_env_path = _cloud_env
    else:
        load_dotenv(_default_env, override=True)
        _loaded_env_path = _default_env
else:
    load_dotenv(_default_env, override=True)
    _loaded_env_path = _default_env

if _loaded_env_path:
    print(f"DB config loaded from: {_loaded_env_path}")

def _resolve_settings_path():
    if getattr(sys, "frozen", False):
        # Prefer a user-editable settings file next to the exe.
        return os.path.join(os.path.dirname(sys.executable), "app_settings.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_settings.json")


def _resolve_bundled_settings_path():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "app_settings.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_settings.json")


_APP_SETTINGS_PATH = _resolve_settings_path()
_BUNDLED_SETTINGS_PATH = _resolve_bundled_settings_path()
_KEYRING_SERVICE = "bjjvienna_postgres"
_KEYRING_USER_KEY = "__db_user__"


def _load_app_settings():
    # First try the editable settings file next to the exe (or project root).
    if os.path.exists(_APP_SETTINGS_PATH):
        try:
            with open(_APP_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    # If missing in frozen mode, fall back to the bundled default.
    if os.path.exists(_BUNDLED_SETTINGS_PATH):
        try:
            with open(_BUNDLED_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                data = data if isinstance(data, dict) else {}
            # Try to persist a user-editable copy next to the exe.
            try:
                with open(_APP_SETTINGS_PATH, "w", encoding="utf-8") as out:
                    json.dump(data, out, indent=2, ensure_ascii=False)
            except Exception:
                pass
            return data
        except Exception:
            return {}
    return {}


def _load_db_settings():
    settings = _load_app_settings()
    db_settings = settings.get("db")
    return db_settings if isinstance(db_settings, dict) else {}


def get_client_startup_context():
    db_settings = _load_db_settings()
    host = os.getenv("DB_HOST") or db_settings.get("host")
    port = os.getenv("DB_PORT") or db_settings.get("port")
    dbname = os.getenv("DB_NAME") or db_settings.get("name")
    env_source = _loaded_env_path if _loaded_env_path and os.path.exists(_loaded_env_path) else "none"
    return {
        "env": _env,
        "db_host": host or "",
        "db_port": str(port or ""),
        "db_name": dbname or "",
        "env_source": env_source,
    }


def _save_app_settings(settings):
    try:
        with open(_APP_SETTINGS_PATH, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _get_keyring_user():
    return keyring.get_password(_KEYRING_SERVICE, _KEYRING_USER_KEY)


def _get_keyring_password(user):
    if not user:
        return None
    return keyring.get_password(_KEYRING_SERVICE, user)


def _save_keyring_credentials(user, password):
    keyring.set_password(_KEYRING_SERVICE, _KEYRING_USER_KEY, user)
    keyring.set_password(_KEYRING_SERVICE, user, password)


def _prompt_for_credentials(default_user=None):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    user = default_user
    if not user:
        user = simpledialog.askstring(
            "Database Login",
            "Database username:",
            parent=root,
        )

    password_prompt = "Database password:" if not user else f"Password for {user}:"
    password = simpledialog.askstring(
        "Database Login",
        password_prompt,
        show="*",
        parent=root,
    )

    if not user or not password:
        messagebox.showerror("Database Login", "Database credentials are required.")
        root.destroy()
        raise RuntimeError("Database credentials are required.")

    root.destroy()
    return user, password


def _prompt_for_db_settings(current):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    host = simpledialog.askstring(
        "Database Settings",
        "Database host:",
        initialvalue=current.get("host", ""),
        parent=root,
    )
    port = simpledialog.askstring(
        "Database Settings",
        "Database port:",
        initialvalue=str(current.get("port", 5432)),
        parent=root,
    )
    name = simpledialog.askstring(
        "Database Settings",
        "Database name:",
        initialvalue=current.get("name", ""),
        parent=root,
    )
    sslmode = simpledialog.askstring(
        "Database Settings",
        "SSL mode (disable/allow/prefer/require/verify-ca/verify-full):",
        initialvalue=current.get("sslmode", "prefer"),
        parent=root,
    )

    root.destroy()

    if not host or not port or not name:
        raise RuntimeError("Database host, port, and name are required.")

    try:
        port_int = int(port)
    except ValueError:
        raise RuntimeError("Database port must be a number.")

    return {
        "host": host.strip(),
        "port": port_int,
        "name": name.strip(),
        "sslmode": (sslmode or "prefer").strip(),
    }


def _require(value, name, hint):
    if value is None or value == "":
        raise RuntimeError(f"Missing database {name}. {hint}")
    return value


_conn = None

def _connect(host, port, dbname, user, password, sslmode):
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode=sslmode,
    )


def _ensure_connection():
    raise RuntimeError(
        "Direct DB access is disabled in API-only mode. Use backend API endpoints instead."
    )


def execute(query, params=None):
    conn = _ensure_connection()
    with conn.cursor() as cur:
        cur.execute(query, params or ())
        if cur.description:
            return cur.fetchall()
        return []
