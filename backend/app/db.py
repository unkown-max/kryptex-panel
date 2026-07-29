"""
Local metadata only. PasarGuard itself remains the single source of truth for
accounts and credentials - we never store a reseller's password here. This
table only holds the extra display info Kryptex shows in the dashboard
(display name, plan label, notes) keyed by the PasarGuard admin username.
"""
import sqlite3
from contextlib import contextmanager

from .config import DB_PATH


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reseller_meta (
                username TEXT PRIMARY KEY,
                display_name TEXT,
                plan TEXT,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def upsert_reseller_meta(username: str, display_name: str, plan: str, note: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO reseller_meta (username, display_name, plan, note)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                display_name=excluded.display_name,
                plan=excluded.plan,
                note=excluded.note
            """,
            (username, display_name, plan, note),
        )
        conn.commit()


def get_reseller_meta(username: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM reseller_meta WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None


def get_all_reseller_meta() -> dict[str, dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM reseller_meta").fetchall()
        return {row["username"]: dict(row) for row in rows}


def delete_reseller_meta(username: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM reseller_meta WHERE username = ?", (username,))
        conn.commit()
