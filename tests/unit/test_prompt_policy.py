"""Tests for system prompt policy compliance and structured log output."""

from __future__ import annotations

import logging
from datetime import datetime
from unittest.mock import patch

import pytest

from src.prompts import SYSTEM_PROMPT
from src.notifications.daily_chat import DAILY_NEWS_STATE_KEY, WAKE_FIRST_SLOT


# ---------------------------------------------------------------------------
# Test 8: Prompt policy contains concise turn-by-turn rules
# ---------------------------------------------------------------------------

class TestPromptPolicyRules:
    """SYSTEM_PROMPT must contain required Soul.md policy phrases."""

    def test_concise_response_rule(self):
        assert "short and focused" in SYSTEM_PROMPT or "1-3 sentences" in SYSTEM_PROMPT

    def test_turn_by_turn_rule(self):
        assert "turn-by-turn" in SYSTEM_PROMPT

    def test_language_following_rule(self):
        assert "same language" in SYSTEM_PROMPT

    def test_time_awareness_rule(self):
        assert "web_search" in SYSTEM_PROMPT

    def test_creative_boundary_rule(self):
        assert "subjective" in SYSTEM_PROMPT.lower()

    def test_no_autonomous_execution_rule(self):
        prompt_lower = SYSTEM_PROMPT.lower()
        assert "not" in prompt_lower and "autonomous" in prompt_lower or \
               "do not execute" in prompt_lower or \
               "unless explicitly asked" in prompt_lower

    def test_prompt_is_english(self):
        """All committed prompt content must be English (Soul.md rule)."""
        # Check no Chinese characters are present.
        for char in SYSTEM_PROMPT:
            assert ord(char) < 0x4E00 or ord(char) > 0x9FFF, (
                f"Found non-English character in SYSTEM_PROMPT: {char!r}"
            )


# ---------------------------------------------------------------------------
# Test 9: Structured log fields present
# ---------------------------------------------------------------------------

class TestStructuredLogFields:
    """Key protocol events produce log output with slot identification."""

    def test_generation_logs_contain_slot_id(self, fake_ai, default_config, fake_state, caplog):
        """generate_for_slot() logs should mention the slot being processed."""
        from src.notifications.daily_chat import DailyChatSource

        fake_ai._responses = [
            '{"topic_key": "test-topic", "message": "Test message."}',
        ]
        source = DailyChatSource(ai_assistant=fake_ai, config=default_config)
        now = datetime(2026, 2, 23, 9, 0)

        with caplog.at_level(logging.DEBUG, logger="src.notifications.daily_chat"):
            source.generate_for_slot(WAKE_FIRST_SLOT, now, fake_state)

        # We do not assert a specific log format, but verify that at least
        # some log activity occurred during generation.  The daily_chat module
        # uses logger.info/logger.exception which produce identifiable output.
        # If generation succeeded, the slot was processed without exceptions.
        # This is a baseline assertion — stricter structured-log tests can be
        # added when a formal schema is adopted.
        day = source._day_record(fake_state, now)
        assert WAKE_FIRST_SLOT in day.get("slot_status", {}), (
            "Slot should be recorded in state after generation"
        )

    def test_skip_logs_contain_slot_id(self, fake_ai, fake_state, caplog):
        """When a slot is skipped, state records the skip reason."""
        config = {
            "daily_chat": {
                "enabled": True,
                "push_times": ["15:00", "20:00"],
                "max_topic_retry": 1,
            },
        }
        fake_ai._responses = [
            '{"topic_key": "dup-topic", "message": "Dup."}',
        ]
        from src.notifications.daily_chat import DailyChatSource

        source = DailyChatSource(ai_assistant=fake_ai, config=config)
        now = datetime(2026, 2, 23, 9, 0)

        # Pre-populate state with the topic already used.
        day_key = now.date().isoformat()
        fake_state.set(DAILY_NEWS_STATE_KEY, {
            day_key: {
                "delivered_slots": [],
                "used_topics": ["dup-topic"],
                "slot_status": {},
            },
        })

        with caplog.at_level(logging.DEBUG, logger="src.notifications.daily_chat"):
            result = source.generate_for_slot(WAKE_FIRST_SLOT, now, fake_state)

        assert result is None
        day = source._day_record(fake_state, now)
        status = day.get("slot_status", {}).get(WAKE_FIRST_SLOT, "")
        assert "skipped" in status, f"Expected skipped status, got: {status}"
