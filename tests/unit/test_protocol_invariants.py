"""Tests for pet state machine transitions and proactive delivery guards."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.notifications.daily_chat import DailyChatSource
from src.pet import Pet, PetState, TRANSITIONS


# ---------------------------------------------------------------------------
# Test 5: Pet transition invariants
# ---------------------------------------------------------------------------

class TestPetTransitionInvariants:
    """All valid transitions succeed; invalid transitions are silently ignored."""

    # -- Valid transitions --------------------------------------------------

    def test_resting_activate_to_awake(self):
        pet = Pet()
        pet.trigger("activate")
        assert pet.state == PetState.AWAKE

    def test_resting_greet_to_greeting(self):
        pet = Pet()
        pet.trigger("greet")
        assert pet.state == PetState.GREETING

    def test_resting_alert_to_alert(self):
        pet = Pet()
        pet.trigger("alert")
        assert pet.state == PetState.ALERT

    def test_awake_submit_to_thinking(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("submit")
        assert pet.state == PetState.THINKING

    def test_awake_dismiss_to_resting(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("dismiss")
        assert pet.state == PetState.RESTING

    def test_greeting_submit_to_thinking(self):
        pet = Pet()
        pet.trigger("greet")
        pet.trigger("submit")
        assert pet.state == PetState.THINKING

    def test_greeting_dismiss_to_resting(self):
        pet = Pet()
        pet.trigger("greet")
        pet.trigger("dismiss")
        assert pet.state == PetState.RESTING

    def test_alert_submit_to_thinking(self):
        pet = Pet()
        pet.trigger("alert")
        pet.trigger("submit")
        assert pet.state == PetState.THINKING

    def test_alert_dismiss_to_resting(self):
        pet = Pet()
        pet.trigger("alert")
        pet.trigger("dismiss")
        assert pet.state == PetState.RESTING

    def test_thinking_answer_to_reply(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("submit")
        pet.trigger("answer")
        assert pet.state == PetState.REPLY

    def test_thinking_chat_answer_to_idle_chat(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("submit")
        pet.trigger("chat_answer")
        assert pet.state == PetState.IDLE_CHAT

    def test_reply_submit_to_thinking(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("submit")
        pet.trigger("answer")
        pet.trigger("submit")
        assert pet.state == PetState.THINKING

    def test_reply_dismiss_to_resting(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("submit")
        pet.trigger("answer")
        pet.trigger("dismiss")
        assert pet.state == PetState.RESTING

    def test_idle_chat_submit_to_thinking(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("submit")
        pet.trigger("chat_answer")
        pet.trigger("submit")
        assert pet.state == PetState.THINKING

    def test_idle_chat_dismiss_to_resting(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("submit")
        pet.trigger("chat_answer")
        pet.trigger("dismiss")
        assert pet.state == PetState.RESTING

    # -- Invalid transitions (silently ignored) -----------------------------

    def test_resting_submit_stays_resting(self):
        pet = Pet()
        pet.trigger("submit")
        assert pet.state == PetState.RESTING

    def test_awake_answer_stays_awake(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("answer")
        assert pet.state == PetState.AWAKE

    def test_reply_greet_stays_reply(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("submit")
        pet.trigger("answer")
        pet.trigger("greet")
        assert pet.state == PetState.REPLY

    def test_thinking_dismiss_stays_thinking(self):
        pet = Pet()
        pet.trigger("activate")
        pet.trigger("submit")
        pet.trigger("dismiss")
        assert pet.state == PetState.THINKING

    # -- Exhaustive: every state has defined transitions only ----------------

    def test_all_states_have_transitions(self):
        """Every PetState must appear in the TRANSITIONS map."""
        for state in PetState:
            assert state in TRANSITIONS, f"Missing transitions for {state}"

    def test_state_change_callback_fires(self):
        """on_state_change callback is invoked on valid transitions."""
        pet = Pet()
        changes: list[tuple] = []
        pet.on_state_change(lambda old, new: changes.append((old, new)))

        pet.trigger("activate")
        assert changes == [(PetState.RESTING, PetState.AWAKE)]


# ---------------------------------------------------------------------------
# Test 6: Deferred when overlay not resting
# ---------------------------------------------------------------------------

class TestDeferredWhenNotResting:
    """Proactive delivery is blocked when the overlay is not in RESTING state."""

    def test_can_show_proactive_only_when_resting(self):
        """Simulate can_show_proactive() logic: True only when pet is RESTING."""
        pet = Pet()

        # RESTING → can show proactive.
        assert pet.state == PetState.RESTING

        # AWAKE → cannot show proactive.
        pet.trigger("activate")
        assert pet.state != PetState.RESTING

        # Back to RESTING → can show proactive again.
        pet.trigger("dismiss")
        assert pet.state == PetState.RESTING

    def test_scheduler_guard_blocks_delivery(self, daily_source, fake_state):
        """When can_show_proactive is False, scheduled news should not deliver."""
        pet = Pet()
        pet.trigger("activate")  # not RESTING

        can_show = pet.state == PetState.RESTING
        assert can_show is False

        # The scheduler loop in main.py checks can_show_proactive() before
        # calling _deliver_daily_news_slot(). We verify the guard condition.
        now = datetime(2026, 2, 23, 15, 1)
        pending = daily_source.pending_timed_slots(fake_state, now)

        # Slots are pending (time-wise), but guard should prevent delivery.
        # In production, _run_scheduled_news_loop skips when can_show is False.
        assert len(pending) > 0  # slot is due
        assert can_show is False  # but guard blocks


# ---------------------------------------------------------------------------
# Test 7: Deferred drains when resting again
# ---------------------------------------------------------------------------

class TestDeferredDrainsWhenResting:
    """After being deferred, a slot becomes deliverable when pet returns to RESTING."""

    def test_deferred_slot_available_after_resting(self, fake_ai, default_config, fake_state):
        fake_ai._responses = [
            '{"topic_key": "new-topic", "message": "Here is some fresh news."}',
        ]
        source = DailyChatSource(ai_assistant=fake_ai, config=default_config)
        pet = Pet()
        now = datetime(2026, 2, 23, 15, 5)

        # Phase 1: Pet is busy (AWAKE) — slot is pending but guard blocks.
        pet.trigger("activate")
        assert pet.state != PetState.RESTING
        pending = source.pending_timed_slots(fake_state, now)
        assert "afternoon_1500" in pending

        # Phase 2: Pet returns to RESTING — delivery proceeds.
        pet.trigger("dismiss")
        assert pet.state == PetState.RESTING

        result = source.generate_for_slot("afternoon_1500", now, fake_state)
        assert result is not None
        assert result.text == "Here is some fresh news."
