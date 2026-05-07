from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from app.accounting import NormalizedLine


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "accounting_demo.sqlite3"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                ocr_text TEXT NOT NULL,
                prompt TEXT NOT NULL,
                model_response TEXT NOT NULL,
                normalized_json TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS journal_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id INTEGER NOT NULL,
                transaction_no INTEGER NOT NULL,
                transaction_date TEXT NOT NULL,
                account TEXT NOT NULL,
                description TEXT NOT NULL,
                debit INTEGER NOT NULL DEFAULT 0,
                credit INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(upload_id) REFERENCES uploads(id) ON DELETE CASCADE
            )
            """
        )


def save_result(
    *,
    original_filename: str,
    stored_filename: str,
    content_type: str,
    file_size: int,
    ocr_text: str,
    prompt: str,
    model_response: str,
    normalized: dict[str, Any],
    lines: list[NormalizedLine],
    error_message: str | None = None,
) -> int:
    normalized_json = json.dumps(normalized, ensure_ascii=False)
    status = str(normalized.get("status", "unknown"))

    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO uploads (
                    original_filename, stored_filename, content_type, file_size,
                    ocr_text, prompt, model_response, normalized_json, status, error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    original_filename,
                    stored_filename,
                    content_type,
                    file_size,
                    ocr_text,
                    prompt,
                    model_response,
                    normalized_json,
                    status,
                    error_message,
                ),
            )
            upload_id = int(cursor.lastrowid)
            conn.executemany(
                """
                INSERT INTO journal_lines (
                    upload_id, transaction_no, transaction_date, account,
                    description, debit, credit
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        upload_id,
                        line.transaction_no,
                        line.transaction_date,
                        line.account,
                        line.description,
                        line.debit,
                        line.credit,
                    )
                    for line in lines
                ],
            )
            return upload_id
    except sqlite3.Error:
        logger.exception("SQLite write failed")
        raise


def get_recent_uploads(limit: int = 5) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, original_filename, stored_filename, status, created_at
            FROM uploads
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
