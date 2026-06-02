"""Migration: add audio_seconds_in / audio_seconds_out to sessions table.

Run once: python migrate_add_audio_columns.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from config.settings import settings


def migrate() -> None:
    db_path = Path(settings.SQLITE_PATH)
    if not db_path.exists():
        print(f"Database not found at {db_path}, nothing to migrate.")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(sessions)")
    columns = {row[1] for row in cursor.fetchall()}

    if "audio_seconds_in" not in columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN audio_seconds_in FLOAT NOT NULL DEFAULT 0.0")
        print("Added audio_seconds_in column.")
    else:
        print("audio_seconds_in column already exists, skipping.")

    if "audio_seconds_out" not in columns:
        cursor.execute("ALTER TABLE sessions ADD COLUMN audio_seconds_out FLOAT NOT NULL DEFAULT 0.0")
        print("Added audio_seconds_out column.")
    else:
        print("audio_seconds_out column already exists, skipping.")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
