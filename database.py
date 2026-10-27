from pathlib import Path
import sqlite3
from typing import Any


DATABASE_PATH = Path(__file__).parent / "database" / "students.db"


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                risk_probability REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_prediction(student_name: str, risk_level: str, probability: float) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO predictions (student_name, risk_level, risk_probability) VALUES (?, ?, ?)",
            (student_name, risk_level, probability),
        )


def recent_predictions(limit: int = 6) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT student_name, risk_level, risk_probability, created_at FROM predictions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def prediction_summary() -> dict[str, int]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total, SUM(CASE WHEN risk_level = 'High' THEN 1 ELSE 0 END) AS high, "
            "SUM(CASE WHEN risk_level = 'Medium' THEN 1 ELSE 0 END) AS medium FROM predictions"
        ).fetchone()
    return {"total": row["total"] or 0, "high": row["high"] or 0, "medium": row["medium"] or 0}
