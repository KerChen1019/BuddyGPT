"""Pet state machine for the desktop Shiba assistant."""

import time
from enum import Enum
from dataclasses import dataclass


class PetState(Enum):
    SLEEPING = "sleeping"       # Default idle — eyes closed, breathing animation
    WAKING = "waking"           # Transition — open eyes, stretch, look around
    LISTENING = "listening"     # Waiting for user input — ears up, alert
    THINKING = "thinking"       # AI processing — head tilt, tail wag
    ANSWERING = "answering"     # Showing response — happy face, speech bubble
    RESTING = "resting"         # Transition back — yawn, lie down, close eyes


# How long each transition state lasts before auto-advancing
STATE_DURATIONS = {
    PetState.WAKING: 0.8,      # seconds
    PetState.RESTING: 1.2,
}

# State transitions
TRANSITIONS = {
    PetState.SLEEPING:  {"activate": PetState.WAKING},
    PetState.WAKING:    {"auto": PetState.LISTENING},
    PetState.LISTENING: {"submit": PetState.THINKING, "dismiss": PetState.RESTING},
    PetState.THINKING:  {"answer": PetState.ANSWERING},
    PetState.ANSWERING: {"submit": PetState.THINKING, "dismiss": PetState.RESTING},
    PetState.RESTING:   {"auto": PetState.SLEEPING},
}

# Emoji shorthand for each state (used in UI until real sprites are ready)
STATE_EMOJI = {
    PetState.SLEEPING:  "💤",
    PetState.WAKING:    "👀",
    PetState.LISTENING: "🐕",
    PetState.THINKING:  "🤔",
    PetState.ANSWERING: "😊",
    PetState.RESTING:   "😴",
}

# Opacity per state (0.0 – 1.0)
STATE_OPACITY = {
    PetState.SLEEPING:  0.7,
    PetState.WAKING:    1.0,
    PetState.LISTENING: 1.0,
    PetState.THINKING:  1.0,
    PetState.ANSWERING: 1.0,
    PetState.RESTING:   0.85,
}


@dataclass
class PetAnimation:
    """Info about the current animation frame to render."""
    state: PetState
    emoji: str
    opacity: float
    frame_index: int
    show_input: bool
    show_bubble: bool


class Pet:
    def __init__(self):
        self.state = PetState.SLEEPING
        self._state_entered = time.time()
        self._frame_index = 0
        self._on_state_change: list = []

    def on_state_change(self, callback):
        """Register callback(old_state, new_state)."""
        self._on_state_change.append(callback)

    def trigger(self, event: str):
        """Trigger a state transition. Events: activate, submit, answer, dismiss."""
        transitions = TRANSITIONS.get(self.state, {})
        next_state = transitions.get(event)
        if next_state:
            self._change_state(next_state)

    def tick(self):
        """Called periodically. Handles auto-transitions and frame counting."""
        self._frame_index += 1

        # Auto-advance timed states
        duration = STATE_DURATIONS.get(self.state)
        if duration and (time.time() - self._state_entered) >= duration:
            auto_next = TRANSITIONS.get(self.state, {}).get("auto")
            if auto_next:
                self._change_state(auto_next)

    def get_animation(self) -> PetAnimation:
        """Get current animation info for rendering."""
        return PetAnimation(
            state=self.state,
            emoji=STATE_EMOJI.get(self.state, "🐕"),
            opacity=STATE_OPACITY.get(self.state, 1.0),
            frame_index=self._frame_index,
            show_input=self.state in (PetState.LISTENING, PetState.ANSWERING),
            show_bubble=self.state == PetState.ANSWERING,
        )

    def _change_state(self, new_state: PetState):
        old = self.state
        self.state = new_state
        self._state_entered = time.time()
        self._frame_index = 0
        for cb in self._on_state_change:
            cb(old, new_state)
