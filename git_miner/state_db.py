import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class StateDB:
    """SQLite database for saving application state (saved searches, etc.)."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_path = Path.home() / ".cache" / "git-miner" / "state.db"
        self.db_path = db_path
        self._is_memory = isinstance(db_path, str) and db_path == ":memory:"
        self._conn: sqlite3.Connection | None = None

        if not self._is_memory:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        if self._is_memory and self._conn is not None:
            return self._conn
        if self._is_memory:
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
            return self._conn
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        """Initialize SQLite database with tables."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS saved_searches (
                    name TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    options TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def close(self) -> None:
        """Close the database connection if using in-memory database."""
        if self._is_memory and self._conn:
            self._conn.close()
            self._conn = None

    def save_search(
        self, name: str, query: str, options: dict[str, Any], force: bool = False
    ) -> None:
        """Save a search query with options.

        Args:
            name: Name for the saved search
            query: Search query string
            options: Dictionary of search options
            force: Overwrite existing search if True

        Raises:
            ValueError: If search already exists and force is False
        """
        options_json = json.dumps(options, default=str)
        now_iso = datetime.now(UTC).isoformat()

        with self._get_connection() as conn:
            if not force:
                cursor = conn.execute("SELECT name FROM saved_searches WHERE name = ?", (name,))
                if cursor.fetchone():
                    raise ValueError(
                        f"Saved search '{name}' already exists. Use --force to overwrite."
                    )

            conn.execute(
                """
                INSERT INTO saved_searches (name, query, options, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    query = excluded.query,
                    options = excluded.options,
                    updated_at = excluded.updated_at
            """,
                (name, query, options_json, now_iso, now_iso),
            )
            conn.commit()

    def get_search(self, name: str) -> dict[str, Any] | None:
        """Get a saved search by name.

        Args:
            name: Name of saved search

        Returns:
            Dictionary with query and options, or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT query, options, created_at, updated_at FROM saved_searches WHERE name = ?",
                (name,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "name": name,
                    "query": row[0],
                    "options": json.loads(row[1]),
                    "created_at": row[2],
                    "updated_at": row[3],
                }
            return None

    def list_searches(self) -> list[dict[str, Any]]:
        """List all saved searches.

        Returns:
            List of saved search metadata
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT name, query, created_at, updated_at "
                "FROM saved_searches ORDER BY updated_at DESC"
            )
            return [
                {
                    "name": row[0],
                    "query": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                }
                for row in cursor.fetchall()
            ]

    def delete_search(self, name: str) -> None:
        """Delete a saved search.

        Args:
            name: Name of the search to delete

        Raises:
            ValueError: If search not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM saved_searches WHERE name = ?", (name,))
            if cursor.rowcount == 0:
                raise ValueError(f"Saved search '{name}' not found.")
            conn.commit()
