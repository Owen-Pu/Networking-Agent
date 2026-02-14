"""SQLite database for deduplication."""

import sqlite3
import logging
from pathlib import Path
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class DedupeDatabase:
    """SQLite database for tracking seen URLs."""

    def __init__(self, db_path: str):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._initialize_schema()

    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")

    def _initialize_schema(self):
        """Create tables if they don't exist."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r") as f:
            schema_sql = f.read()

        self.conn.executescript(schema_sql)
        self.conn.commit()
        logger.debug("Database schema initialized")

    def is_seen(self, url: str) -> bool:
        """
        Check if URL has been processed before.

        Args:
            url: URL to check

        Returns:
            True if URL exists in database
        """
        cursor = self.conn.execute(
            "SELECT 1 FROM seen_urls WHERE url = ? LIMIT 1", (url,)
        )
        result = cursor.fetchone()
        return result is not None

    def mark_seen(self, url: str, item_type: str = "article"):
        """
        Mark URL as seen.

        Args:
            url: URL to mark as seen
            item_type: Type of item ('article', 'company', 'person')
        """
        try:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO seen_urls (url, item_type, last_updated)
                VALUES (?, ?, ?)
                """,
                (url, item_type, datetime.now()),
            )
            self.conn.commit()
            logger.debug(f"Marked as seen: {url} ({item_type})")
        except Exception as e:
            logger.error(f"Failed to mark URL as seen: {e}")
            raise

    def get_stats(self) -> Dict[str, int]:
        """
        Get database statistics.

        Returns:
            Dictionary with counts by item type
        """
        cursor = self.conn.execute(
            """
            SELECT item_type, COUNT(*) as count
            FROM seen_urls
            GROUP BY item_type
            """
        )
        stats = {row["item_type"]: row["count"] for row in cursor.fetchall()}

        # Add total count
        cursor = self.conn.execute("SELECT COUNT(*) as total FROM seen_urls")
        stats["total"] = cursor.fetchone()["total"]

        return stats

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
