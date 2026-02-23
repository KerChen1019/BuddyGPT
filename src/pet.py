"""Pet state machine for the desktop Shiba assistant."""

import time
from enum import Enum
from dataclasses import dataclass


class PetState(Enum):
    RESTING = "resting"       # Default idle — relaxed, looping animation
    GREETING = "greeting"     # Daily proactive opener
    ALERT = "alert"           # Urgent proactive notification
    AWAKE = "awake"           # Activated — alert, ready for input
    THINKING = "thinking"     # AI processing — working animation
    REPLY = "reply"           # Showing response — talking animation
    IDLE_CHAT = "idle_chat"   # Relaxed reply after proactive greeting


# State transitions
TRANSITIONS = {
    PetState.RESTING:  {
        "activate": PetState.AWAKE,
        "greet": PetState.GREETING,
        "alert": PetState.ALERT,
    },
    PetState.GREETING: {"submit": PetState.THINKING, "dismiss": PetState.RESTING},
    PetState.ALERT:    {"submit": PetState.THINKING, "dismiss": PetState.RESTING},
    PetState.AWAKE:    {"submit": PetState.THINKING, "dismiss": PetState.RESTING},
    PetState.THINKING: {"answer": PetState.REPLY, "chat_answer": PetState.IDLE_CHAT},
    PetState.REPLY:    {"submit": PetState.THINKING, "dismiss": PetState.RESTING},
    PetState.IDLE_CHAT: {"submit": PetState.THINKING, "dismiss": PetState.RESTING},
}

# Opacity per state
STATE_OPACITY = {
    PetState.RESTING:  0.85,
    PetState.GREETING: 1.0,
    PetState.ALERT:    1.0,
    PetState.AWAKE:    1.0,
    PetState.THINKING: 1.0,
    PetState.REPLY:    1.0,
    PetState.IDLE_CHAT: 1.0,
}


@dataclass
class PetAnimation:
    """Info about the current animation frame to render."""
    state: PetState
    opacity: float
    frame_index: int
    show_input: bool
    show_bubble: bool


class Pet:
    def __init__(self):
        self.state = PetState.RESTING
        self._state_entered = time.time()
        self._frame_index = 0
        self._on_state_change: list = []

    def on_state_change(self, callback):
        """Register callback(old_state, new_state)."""
        self._on_state_change.append(callback)

    def trigger(self, event: str):
        """Trigger a state transition."""
        transitions = TRANSITIONS.get(self.state, {})
        next_state = transitions.get(event)
        if next_state:
            self._change_state(next_state)

    def tick(self):
        """Called periodically. Advances frame counter."""
        self._frame_index += 1

    def get_animation(self) -> PetAnimation:
        """Get current animation info for rendering."""
        return PetAnimation(
            state=self.state,
            opacity=STATE_OPACITY.get(self.state, 1.0),
            frame_index=self._frame_index,
            show_input=self.state in (
                PetState.AWAKE,
                PetState.GREETING,
                PetState.ALERT,
                PetState.REPLY,
                PetState.IDLE_CHAT,
            ),
            show_bubble=self.state in (
                PetState.THINKING,
                PetState.GREETING,
                PetState.ALERT,
                PetState.REPLY,
                PetState.IDLE_CHAT,
            ),
        )

    def _change_state(self, new_state: PetState):
        old = self.state
        self.state = new_state
        self._state_entered = time.time()
        self._frame_index = 0
        for cb in self._on_state_change:
            cb(old, new_state)
