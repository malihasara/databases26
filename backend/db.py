from contextlib import contextmanager
import mysql.connector
from flask import current_app, g


def get_connection():
    cfg = current_app.config
    return mysql.connector.connect(
        host=cfg["DB_HOST"],
        port=cfg["DB_PORT"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        database=cfg["DB_NAME"],
        autocommit=False,
        connection_timeout=10,
    )


def get_db():
    if "db" not in g:
        g.db = get_connection()
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def cursor(dictionary=True):
    conn = get_db()
    cur = conn.cursor(dictionary=dictionary)
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def query(sql, params=None, one=False):
    with cursor() as cur:
        cur.execute(sql, params or ())
        rows = cur.fetchall()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=None):
    with cursor() as cur:
        cur.execute(sql, params or ())
        return cur.lastrowid


def call_proc(name, args):
    placeholders = ",".join(["%s"] * len(args))
    with cursor(dictionary=False) as cur:
        cur.execute(f"CALL {name}({placeholders})", tuple(args))
        while cur.nextset():
            pass


def next_id(prefix: str, table: str, column: str) -> str:
    row = query(
        f"SELECT {column} AS id FROM {table} "
        f"WHERE {column} LIKE %s ORDER BY {column} DESC LIMIT 1",
        (f"{prefix}%",),
        one=True,
    )
    if not row:
        return f"{prefix}001"
    n = int(row["id"][len(prefix):]) + 1
    return f"{prefix}{n:03d}"
