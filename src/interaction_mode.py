"""Interaction mode types for content-aware response routing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResponseMode(str, Enum):
    """Assistant response posture for sprite/state mapping."""

    WORK = "work"
    CASUAL = "casual"


@dataclass(slots=True)
class AssistantTurnResult:
    """Result payload returned by on_submit for overlay rendering."""

    text: str
    response_mode: ResponseMode
