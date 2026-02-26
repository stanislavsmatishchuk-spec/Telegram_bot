

import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = "reminders.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                text        TEXT NOT NULL,
                remind_at   TEXT NOT NULL,
                sent        INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        conn.commit()
        logger.info("Database initialized successfully.")



def upsert_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name))
        conn.commit()



def add_reminder(user_id: int, text: str, remind_at: datetime) -> int:
    remind_at_str = remind_at.strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO reminders (user_id, text, remind_at)
            VALUES (?, ?, ?)
        """, (user_id, text, remind_at_str))
        conn.commit()
        return cursor.lastrowid


def get_reminders(user_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, text, remind_at
            FROM reminders
            WHERE user_id = ? AND sent = 0
            ORDER BY remind_at ASC
        """, (user_id,)).fetchall()
    return rows


def delete_reminder(reminder_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM reminders
            WHERE id = ? AND user_id = ?
        """, (reminder_id, user_id))
        conn.commit()
        return cursor.rowcount > 0


def get_pending_reminders() -> list[sqlite3.Row]:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, user_id, text, remind_at
            FROM reminders
            WHERE sent = 0 AND remind_at <= ?
            ORDER BY remind_at ASC
        """, (now_str,)).fetchall()
    return rows


def mark_reminder_sent(reminder_id: int) -> None:
    with get_connection() as conn:
        conn.execute("""
            UPDATE reminders SET sent = 1
            WHERE id = ?
        """, (reminder_id,))
        conn.commit()
