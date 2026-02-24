"""
Tracks which DM messages have been processed to avoid duplicates.
Uses a simple JSON file for persistence.
"""

import json
import logging
import os
from typing import Set

logger = logging.getLogger(__name__)

TRACKER_FILE = "processed.json"


class Tracker:
    """Tracks processed message IDs to prevent duplicate reposts."""

    def __init__(self, filepath: str = TRACKER_FILE):
        self.filepath = filepath
        self.processed_ids: Set[str] = set()
        self._load()

    def _load(self):
        """Load processed IDs from disk."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get("processed", []))
                logger.info(f"📋 Loaded {len(self.processed_ids)} processed message IDs.")
            except (json.JSONDecodeError, KeyError):
                logger.warning("⚠️  Corrupted tracker file. Starting fresh.")
                self.processed_ids = set()
        else:
            logger.info("📋 No processed messages yet. Starting fresh.")

    def _save(self):
        """Persist processed IDs to disk."""
        with open(self.filepath, "w") as f:
            json.dump({"processed": list(self.processed_ids)}, f, indent=2)

    def is_processed(self, message_id: str) -> bool:
        """Check if a message has already been processed."""
        return str(message_id) in self.processed_ids

    def mark_processed(self, message_id: str):
        """Mark a message as processed and save."""
        self.processed_ids.add(str(message_id))
        self._save()
        logger.debug(f"   Marked message {message_id} as processed.")
