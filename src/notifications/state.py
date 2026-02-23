"""Persistent runtime state for notifications."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from src.config import user_data_dir

logger = logging.getLogger(__name__)


class NotificationState:
    """Simple key-value store persisted to notification_state.json."""

    def __init__(self, path: Path | None = None):
        self._path = path or (user_data_dir() / "notification_state.json")
        self._lock = threading.Lock()
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            self._data = {}
            return
        try:
            self._data = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(self._data, dict):
                self._data = {}
        except (OSError, json.JSONDecodeError):
            logger.warning("Failed to read notification state: %s", self._path)
            self._data = {}

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            logger.exception("Failed to persist notification state: %s", self._path)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self._save()
