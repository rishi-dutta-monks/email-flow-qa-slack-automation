"""
Deduplication store using SQLite to prevent duplicate Slack threads
when Monday statuses are toggled repeatedly.
"""

import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class DedupStore:
    def __init__(self, db_path: str = "email_flow_dedup.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes the database schema if it doesn't exist."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_campaigns (
                    item_id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    campaign_name TEXT NOT NULL,
                    slack_thread_ts TEXT NOT NULL,
                    checklist_url TEXT,
                    created_at TIMESTAMP NOT NULL
                )
                """
            )
            conn.commit()

    def is_processed(self, item_id: str) -> bool:
        """Checks if an item has already generated a Slack thread."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM processed_campaigns WHERE item_id = ?",
                (str(item_id),),
            )
            return cursor.fetchone() is not None

    def get_record(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an existing processing record by item ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM processed_campaigns WHERE item_id = ?",
                (str(item_id),),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def record_success(
        self,
        item_id: str,
        campaign_id: str,
        campaign_name: str,
        slack_thread_ts: str,
        checklist_url: Optional[str] = None,
    ) -> None:
        """Stores a successfully processed campaign and its Slack thread timestamp."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO processed_campaigns 
                (item_id, campaign_id, campaign_name, slack_thread_ts, checklist_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(item_id),
                    str(campaign_id),
                    campaign_name,
                    str(slack_thread_ts),
                    checklist_url,
                    now,
                ),
            )
            conn.commit()
            logger.info(
                f"[DedupStore] Recorded item {item_id} (Campaign {campaign_id}) -> Slack thread {slack_thread_ts}"
            )

    def list_processed(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent processed campaigns."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM processed_campaigns ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
