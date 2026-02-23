"""Shared notification contracts for proactive sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.pet import PetState


@dataclass
class Notification:
    """A generated proactive message ready for UI display."""

    source_id: str
    text: str
    hint: str = ""
    status: str = ""
    priority: str = "normal"
    pet_state: PetState = PetState.GREETING


class NotificationSource(ABC):
    """Interface for a notification source."""

    @property
    @abstractmethod
    def source_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def check(self, state) -> bool:
        """Return True if this source should generate now."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, state) -> Notification | None:
        """Generate a notification payload."""
        raise NotImplementedError
