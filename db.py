import os
import psycopg2
from dotenv import load_dotenv

_env = os.getenv("APP_ENV", "default").lower()
_base_dir = os.path.dirname(os.path.abspath(__file__))
_dev_env = os.path.join(_base_dir, ".env.dev")
_default_env = os.path.join(_base_dir, ".env")
_prod_env = os.path.join(_base_dir, ".env.prod")
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
else:
    load_dotenv(_default_env, override=True)
    _loaded_env_path = _default_env

if _loaded_env_path:
    print(f"DB config loaded from: {_loaded_env_path}")

_conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)


_conn.autocommit = True

def execute(query, params=None):
    with _conn.cursor() as cur:
        cur.execute(query, params or ())
        if cur.description:
            return cur.fetchall()
        return []
