# BuddyGPT Interaction Protocol

Normative specification for Phase 1 Internal Alpha.
This document defines the actors, states, events, invariants, and flows
that govern BuddyGPT's runtime behavior.

---

## 1. Actors

| Actor | Implementation | Role |
|---|---|---|
| **User** | Human operator | Triggers activation, submits questions, dismisses overlay |
| **Overlay UI** | `OverlayWindow` | Renders pet animation, chat bubbles, input bar; manages UI state |
| **Orchestrator** | `main.py` | Wires activation, AI calls, and notification delivery together |
| **AI Runtime** | `AIAssistant` | Executes model calls with optional `web_search` tool use |
| **Notification Scheduler** | `DailyChatSource` + `_run_scheduled_news_loop` | Polls for due time slots and generates proactive content |
| **State Store** | `NotificationState` | Persists daily slot delivery records to `notification_state.json` |

---

## 2. Canonical States

| State | Description | Shows Input | Shows Bubble |
|---|---|---|---|
| `RESTING` | Default idle state. Pet loops resting animation. | No | No |
| `GREETING` | Proactive daily chat greeting displayed. | Yes | Yes |
| `ALERT` | Urgent proactive notification displayed (Phase 2/3). | Yes | Yes |
| `AWAKE` | User activated overlay, ready for question input. | Yes | No |
| `THINKING` | AI is processing the user's question. | No | Yes |
| `REPLY` | AI response displayed after a standard question. | Yes | Yes |
| `IDLE_CHAT` | AI response displayed after a proactive greeting follow-up. | Yes | Yes |

---

## 3. Canonical Events

### User-Driven Events

| Event | Description |
|---|---|
| `ACTIVATE` | User presses hotkey or clicks resting pet |
| `SUBMIT` | User submits a question or reply |
| `DISMISS` | User presses Esc or clicks away |

### AI-Driven Events

| Event | Description |
|---|---|
| `ANSWER` | AI returns a response to a standard question |
| `CHAT_ANSWER` | AI returns a response during chat/greeting mode |
| `AUTO_REST` | Overlay returns to RESTING after inactivity timeout |

### Scheduler Events

| Event | Description |
|---|---|
| `SLOT_DUE` | A timed slot's push_time boundary has passed |
| `SLOT_DELIVERED` | A slot's content was generated and displayed |
| `SLOT_SKIPPED_NO_UNIQUE_TOPIC` | All retry attempts produced duplicate topics |
| `SLOT_DEFERRED_BUSY` | Slot was due but UI was not in RESTING state |
| `SLOT_DRAINED` | A previously deferred slot was delivered on a later cycle |

---

## 4. State Transition Map

```
RESTING   + activate    -> AWAKE
RESTING   + greet       -> GREETING
RESTING   + alert       -> ALERT

AWAKE     + submit      -> THINKING
AWAKE     + dismiss     -> RESTING

GREETING  + submit      -> THINKING
GREETING  + dismiss     -> RESTING

ALERT     + submit      -> THINKING
ALERT     + dismiss     -> RESTING

THINKING  + answer      -> REPLY
THINKING  + chat_answer -> IDLE_CHAT

REPLY     + submit      -> THINKING
REPLY     + dismiss     -> RESTING

IDLE_CHAT + submit      -> THINKING
IDLE_CHAT + dismiss     -> RESTING
```

Invalid event/state combinations are silently ignored.

---

## 5. Invariants

These properties must hold at all times during runtime:

1. **Single session**: At most one active interactive chat session exists at a time.
2. **Proactive gate**: Proactive notifications are displayed only when `overlay.can_show_proactive() == True` (pet is in RESTING state).
3. **Topic uniqueness**: A proactive topic key must not repeat across any slots on the same calendar day.
4. **Non-interrupting**: When a slot becomes due while the pet is not RESTING, behavior is defer (not interrupt).
5. **No cross-day replay**: Deferred slots are same-day only. A new calendar day resets all slot availability.
6. **Language matching**: AI responses follow the language of the user's input.
7. **Concise by default**: Replies are short and turn-by-turn unless the user explicitly requests detail.

---

## 6. Flow A: Manual Activation

```
User presses hotkey / clicks pet
  |
  v
Orchestrator: on_activate()
  |
  +-- If onboarding needed: show onboarding notice -> END
  |
  +-- Acquire news_lock
  |     |
  |     +-- Check wake-first slot eligibility
  |     |     |
  |     |     +-- If should_trigger_slot(wake_first) AND can deliver:
  |     |     |     generate_for_slot(wake_first)
  |     |     |     Pet -> GREETING
  |     |     |     show_notice(greeting)
  |     |     |     -> END
  |     |     |
  |     |     +-- Else: fall through to normal activation
  |     |
  |     +-- Capture active window (get_active_hwnd)
  |     +-- Detect app type (detect_app)
  |     +-- Capture + filter screenshot
  |     +-- Clear AI history
  |     +-- Set app context
  |     +-- Pet -> AWAKE
  |     +-- overlay.show(image, window_title)
  |
  +-- Release news_lock
```

---

## 7. Flow B: Ask/Reply

```
User types question + presses Enter
  |
  v
Overlay: SUBMIT event
  Pet -> THINKING
  |
  v
Orchestrator: on_submit(question, image)
  |
  +-- If onboarding mode: handle API key input -> return text
  |
  +-- Re-capture window if no image
  +-- Prepend app context to question
  +-- Call ai.ask(full_question, image)
  |
  v
AI returns response
  |
  +-- If in chat mode (post-greeting): Pet -> IDLE_CHAT
  +-- Else: Pet -> REPLY
  |
  v
Display response in chat bubble
  |
  +-- User submits follow-up -> loop back to THINKING
  +-- User dismisses (Esc) -> Pet -> RESTING
  +-- Inactivity timeout -> AUTO_REST -> Pet -> RESTING
```

---

## 8. Flow C: Scheduled Proactive

```
Scheduler thread (_run_scheduled_news_loop)
  polls every 20 seconds
  |
  v
Check guards:
  +-- onboarding_needed? -> skip
  +-- daily_chat disabled? -> skip
  +-- can_show_proactive() == False? -> skip (SLOT_DEFERRED_BUSY)
  |
  v
Acquire news_lock (re-check guards under lock)
  |
  v
pending_timed_slots(state, now_local)
  |
  +-- No pending slots -> release lock, continue polling
  |
  +-- Take first pending slot
  |     |
  |     v
  |   generate_for_slot(slot_id, now_local, state)
  |     |
  |     +-- AI generates topic with dedupe retries
  |     |     |
  |     |     +-- Unique topic found:
  |     |     |     Persist SLOT_DELIVERED
  |     |     |     Pet -> GREETING
  |     |     |     show_notice(notification)
  |     |     |
  |     |     +-- All retries exhausted (duplicate topics):
  |     |           Persist SLOT_SKIPPED_NO_UNIQUE_TOPIC
  |     |           No notification shown
  |     |
  |     v
  |   Log outcome
  |
  v
Release news_lock, continue polling
```

---

## 9. Flow D: Deferred Drain

```
A slot became due while pet was AWAKE/THINKING/REPLY/etc.
  -> SLOT_DEFERRED_BUSY (implicit, slot remains pending)

Later scheduler cycle:
  can_show_proactive() == True (pet returned to RESTING)
  |
  v
pending_timed_slots() returns the deferred slot
  (it is still due by time, and not yet in slot_status)
  |
  v
Deliver via Flow C generation path
  -> SLOT_DELIVERED or SLOT_SKIPPED_NO_UNIQUE_TOPIC

Note: Only same-day slots are eligible.
A new calendar day starts fresh; yesterday's deferred slots expire.
```

---

## 10. Failure and Fallback Rules

| Failure | Behavior |
|---|---|
| AI generation exception | Log exception, return None, show normal activation |
| JSON parse failure in daily topic | Retry within `max_topic_retry` bound |
| All retries produce duplicate topics | Mark slot `skipped_no_unique_topic`, no notification |
| Notification state file missing/corrupt | Create fresh default state |
| Scheduler thread exception | Log exception, continue next cycle |
| Overlay UI exception | Log and continue; never crash main loop |
| Wake-first check fails | Fall through to normal activation flow |

---

## 11. Structured Local Logging Schema

Protocol events should include these fields in log output:

| Field | Description | Example |
|---|---|---|
| `event` | Protocol event name | `SLOT_DELIVERED` |
| `flow` | Which flow produced the event | `scheduled_proactive` |
| `slot_id` | Slot identifier | `afternoon_1500` |
| `pet_state` | Pet state at time of event | `RESTING` |
| `result` | Outcome | `delivered`, `skipped`, `deferred` |
| `reason` | Explanation when not delivered | `no_unique_topic` |
| `date` | Calendar date (ISO) | `2026-02-23` |
| `time_local` | Local time (HH:MM:SS) | `15:01:20` |

Phase 1 uses Python `logging` module with key-value formatting.
No remote telemetry sink in Phase 1.
