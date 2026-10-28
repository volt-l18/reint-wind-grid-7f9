import sqlite3
import json
import os
from typing import Optional, Any
from .config import Config

class SQLiteCache:
    def __init__(self, db_path: str = Config.CACHE_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_cache (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT data FROM api_cache WHERE key = ?", (key,))
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def set(self, key: str, value: Any):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO api_cache (key, data) VALUES (?, ?)",
                (key, json.dumps(value))
            )
            conn.commit()

cache = SQLiteCache()
