import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

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
