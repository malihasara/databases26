"""
load_db.py

Bootstrap script: connects with .env credentials and applies sql/setup.sql.
Handles DELIMITER directives so triggers and procedures load cleanly.
"""

import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
SETUP_SQL = ROOT / "sql" / "setup.sql"


def load_env() -> dict:
    load_dotenv(ROOT / ".env")
    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ.get("DB_PORT", 3306)),
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "database": os.environ["DB_NAME"],
        "ssl_disabled": False,
    }


def split_statements(sql: str) -> list[str]:
    statements: list[str] = []
    delimiter = ";"
    buffer: list[str] = []

    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER "):
            tail = "\n".join(buffer).strip()
            if tail:
                statements.append(tail)
            buffer = []
            delimiter = stripped.split(None, 1)[1].strip()
            continue

        buffer.append(line)
        if stripped.endswith(delimiter):
            joined = "\n".join(buffer).strip()
            if joined.endswith(delimiter):
                joined = joined[: -len(delimiter)].strip()
            if joined:
                statements.append(joined)
            buffer = []

    tail = "\n".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def apply_statements(conn, statements: list[str]) -> None:
    cursor = conn.cursor()
    for i, stmt in enumerate(statements, start=1):
        try:
            cursor.execute(stmt)
            while cursor.nextset():
                pass
        except mysql.connector.Error as exc:
            print(f"\n[FAILED at statement {i}]\n{stmt[:300]}\n--> {exc}", file=sys.stderr)
            raise
    conn.commit()
    cursor.close()


def main() -> None:
    cfg = load_env()
    print(f"Connecting to {cfg['host']}:{cfg['port']} as {cfg['user']}...")
    conn = mysql.connector.connect(**cfg)

    print(f"Reading {SETUP_SQL}...")
    statements = split_statements(SETUP_SQL.read_text(encoding="utf-8"))

    print(f"Executing {len(statements)} statements...")
    apply_statements(conn, statements)

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
