"""
PhotoPro SQLite Local Database Management
Manages persistent user settings, print history, and custom presets with auto-repair.
"""
import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.config.settings import AppSettings
from app.config.constants import DEFAULT_DB_PATH

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles local SQLite persistence with schema initialization and corruption recovery."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Creates tables if they do not exist. Recovers if database file is corrupt."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS print_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        photo_name TEXT,
                        paper_size TEXT NOT NULL,
                        photo_size TEXT NOT NULL,
                        copies INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        details TEXT
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS background_presets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        hex_color TEXT NOT NULL,
                        is_default INTEGER DEFAULT 0
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recent_projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        photo_size TEXT,
                        paper_size TEXT,
                        copies INTEGER
                    )
                """)
                conn.commit()
                self._seed_default_presets(cursor, conn)
        except sqlite3.DatabaseError as e:
            logger.error(f"Database corruption detected ({e}). Recreating clean database...")
            self._recover_corrupted_db()

    def _recover_corrupted_db(self):
        """Backs up corrupt file and re-initializes a fresh database."""
        try:
            if os.path.exists(self.db_path):
                corrupt_backup = f"{self.db_path}.corrupt_{int(datetime.now().timestamp())}"
                os.rename(self.db_path, corrupt_backup)
                logger.warning(f"Moved corrupted database to {corrupt_backup}")
            self._init_db()
        except Exception as ex:
            logger.critical(f"Failed to recover database: {ex}")

    def _seed_default_presets(self, cursor: sqlite3.Cursor, conn: sqlite3.Connection):
        """Seeds standard background presets if empty."""
        cursor.execute("SELECT COUNT(*) FROM background_presets")
        count = cursor.fetchone()[0]
        if count == 0:
            defaults = [
                ("Studio White", "#FFFFFF", 1),
                ("Passport Blue", "#1F6FB2", 1),
                ("Light Grey", "#E5E7EB", 1),
                ("Sky Blue", "#38BDF8", 0),
                ("Off White", "#F4F4F5", 0),
            ]
            cursor.executemany(
                "INSERT INTO background_presets (name, hex_color, is_default) VALUES (?, ?, ?)",
                defaults
            )
            conn.commit()

    # --- Settings Operations ---
    def load_settings(self) -> AppSettings:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key = 'app_settings'")
                row = cursor.fetchone()
                if row:
                    data = json.loads(row["value"])
                    return AppSettings.from_dict(data)
        except Exception as e:
            logger.warning(f"Could not load settings from DB: {e}. Using defaults.")
        return AppSettings()

    def save_settings(self, settings: AppSettings) -> bool:
        try:
            data_str = json.dumps(settings.to_dict())
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('app_settings', ?, CURRENT_TIMESTAMP)",
                    (data_str,)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    # --- Print History Operations ---
    def log_print_job(
        self,
        photo_name: str,
        paper_size: str,
        photo_size: str,
        copies: int,
        status: str = "completed",
        details: str = ""
    ) -> bool:
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self._get_connection() as conn:
                conn.execute(
                    """INSERT INTO print_history 
                       (timestamp, photo_name, paper_size, photo_size, copies, status, details)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (ts, photo_name, paper_size, photo_size, copies, status, details)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to log print job: {e}")
            return False

    def get_print_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM print_history ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to get print history: {e}")
            return []

    # --- Background Presets ---
    def get_background_presets(self) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM background_presets ORDER BY is_default DESC, id ASC")
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get presets: {e}")
            return []
