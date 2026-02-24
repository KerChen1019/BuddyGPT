"""Shared pytest fixtures for BuddyGPT unit tests."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.notifications.daily_chat import DailyChatSource
from src.notifications.state import NotificationState


class FakeAI:
    """Minimal AIAssistant stand-in that returns canned JSON without API calls."""

    def __init__(self, responses: list[str] | None = None):
        self._responses = list(responses or [])
        self._call_count = 0
        self.system_prompt = "fake-system-prompt"
        self.max_tokens = 300
        self.history: list = []

    def ask(self, question: str, image=None) -> str:
        if self._call_count < len(self._responses):
            answer = self._responses[self._call_count]
        else:
            answer = '{"topic_key": "fallback-topic", "message": "Nothing new today."}'
        self._call_count += 1
        return answer

    def clear_history(self) -> None:
        self.history.clear()

    def set_app_context(self, app_type: str) -> None:
        pass


@pytest.fixture()
def fake_state(tmp_path: Path) -> NotificationState:
    """NotificationState backed by a temporary JSON file."""
    return NotificationState(path=tmp_path / "notification_state.json")


@pytest.fixture()
def fake_ai() -> FakeAI:
    """A mock AI assistant that returns canned responses."""
    return FakeAI()


@pytest.fixture()
def default_config() -> dict:
    """A valid default config dict matching src/config.py defaults."""
    return {
        "api_key": "sk-test-fake",
        "model": "claude-sonnet-4-20250514",
        "hotkey_activate": "ctrl+shift+space",
        "hotkey_quit": "ctrl+shift+q",
        "screenshot_interval": 3.0,
        "hash_threshold": 12,
        "max_tokens": 1024,
        "daily_chat": {
            "enabled": True,
            "push_times": ["15:00", "20:00"],
            "max_topic_retry": 3,
        },
    }


@pytest.fixture()
def daily_source(fake_ai: FakeAI, default_config: dict) -> DailyChatSource:
    """A DailyChatSource wired to the fake AI and default config."""
    return DailyChatSource(ai_assistant=fake_ai, config=default_config)
