from contextlib import contextmanager

from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from backend.config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_SSLMODE, DB_USER


def _require(value: str, name: str) -> str:
    if not value:
        raise RuntimeError(f"Missing required DB setting: {name}")
    return value


_POOL = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=_require(DB_HOST, "DB_HOST"),
    port=DB_PORT,
    dbname=_require(DB_NAME, "DB_NAME"),
    user=_require(DB_USER, "DB_USER"),
    password=_require(DB_PASSWORD, "DB_PASSWORD"),
    sslmode=DB_SSLMODE,
)


@contextmanager
def get_conn():
    conn = _POOL.getconn()
    try:
        yield conn
    finally:
        _POOL.putconn(conn)


def fetch_all(query: str, params=()):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def fetch_one(query: str, params=()):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()


def execute(query: str, params=()):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()


def execute_returning_one(query: str, params=()):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
        conn.commit()
        return row
