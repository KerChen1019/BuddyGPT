"""Notification orchestrator for proactive sources."""

from __future__ import annotations

import logging
from datetime import date

from .base import Notification, NotificationSource
from .state import NotificationState

logger = logging.getLogger(__name__)


class NotificationManager:
    """Check registered sources and return the first ready notification."""

    def __init__(self, state: NotificationState | None = None):
        self.state = state or NotificationState()
        self._sources: list[NotificationSource] = []

    def register(self, source: NotificationSource) -> None:
        self._sources.append(source)

    def check_pending(self) -> Notification | None:
        for source in self._sources:
            try:
                if not source.check(self.state):
                    continue
                notification = source.generate(self.state)
                if notification is not None:
                    return notification
            except Exception:
                logger.exception("Notification source failed: %s", source.source_id)
        return None

    def mark_delivered(self, source_id: str) -> None:
        self.state.set(f"{source_id}_last_date", date.today().isoformat())
