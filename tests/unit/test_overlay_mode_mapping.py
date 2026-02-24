"""Unit tests for overlay response mode mapping."""

from __future__ import annotations

from src.interaction_mode import AssistantTurnResult, ResponseMode
from src.overlay import _resolve_response_mode


def test_overlay_mapping_work_result():
    event, text, mode = _resolve_response_mode(
        AssistantTurnResult(text="Done", response_mode=ResponseMode.WORK),
        chat_mode=True,
    )
    assert event == "answer"
    assert text == "Done"
    assert mode == ResponseMode.WORK


def test_overlay_mapping_casual_result():
    event, text, mode = _resolve_response_mode(
        AssistantTurnResult(text="Hey", response_mode=ResponseMode.CASUAL),
        chat_mode=False,
    )
    assert event == "chat_answer"
    assert text == "Hey"
    assert mode == ResponseMode.CASUAL


def test_overlay_mapping_legacy_string_uses_chat_mode_default():
    event, text, mode = _resolve_response_mode("legacy", chat_mode=True)
    assert event == "chat_answer"
    assert text == "legacy"
    assert mode == ResponseMode.CASUAL
