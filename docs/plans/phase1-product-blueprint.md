# BuddyGPT Phase 1 Product Blueprint
## Capability Map + End-to-End Interaction Protocol + MVP (Internal Alpha)

## Summary
This plan defines a decision-complete Phase 1 blueprint for BuddyGPT aligned with `Soul.md`, with three deliverables:
1. A 5-domain Capability Map (L1/L2/L3).
2. A full Interaction Protocol spec (state, events, guards, fallback).
3. An MVP scope definition for Internal Alpha with targeted automated tests and local structured logging.

Chosen defaults from this discussion:
- Capability structure: 3-level map, 5 L1 domains.
- Protocol depth: full chain state machine.
- MVP style: runnable + testable + demoable.
- Release audience: Internal alpha.
- Conflict policy: queue and same-day drain.
- Scope bundle: protocol + tests only.
- Test bar: targeted unit suite.
- Telemetry: local structured logs only.
- Test framework: add `pytest`, keep legacy script tests.

## Public APIs / Interfaces / Types
1. Runtime user-facing config (`config.json`) remains unchanged in Phase 1.
2. Runtime feature scope remains unchanged in Phase 1 (no new end-user features required for this plan).
3. New documentation interfaces (authoritative specs):
- `docs/capability-map.md`
- `docs/interaction-protocol.md`
- `docs/mvp-phase1.md`
4. New internal test interfaces:
- Deterministic unit tests for `src/notifications/daily_chat.py`.
- Protocol invariant tests for `src/pet.py` and scheduler guard behavior in `main.py` via mocks.
- Prompt policy tests for `src/prompts.py`.
5. Dev dependency interface:
- Add `requirements-dev.txt` with `pytest>=8` (do not add pytest to runtime `requirements.txt`).

## Capability Map (Decision-Complete)
Create `docs/capability-map.md` with the following fixed structure.

### L1 Domain 1: Core Chat Experience
- L2 App Activation
- L2 Context Capture
- L2 Response Generation
- L2 Follow-up Session
- L3 examples: hotkey/mouse activation, active-window capture, app-aware prompt merge, tool-call loop, auto-rest.

### L1 Domain 2: Proactive Intelligence
- L2 Daily News Scheduler
- L2 Slot Deduplication
- L2 Safe Delivery Gate
- L3 examples: wake-first/15:00/20:00 slots, same-day topic dedupe, RESTING-only proactive display, same-day catch-up drain.

### L1 Domain 3: Safety & Permission Governance
- L2 Advice-First Prompt Policy
- L2 Execution Boundary
- L2 Risk Explanation Policy
- L3 examples: no implicit system-changing actions, technical-boundary response style, safety-first wording constraints.

### L1 Domain 4: Memory & Personalization
- L2 Session Memory
- L2 Reset Semantics
- L2 Privacy Boundary
- L3 examples: in-session history, activation reset points, no broad background indexing behavior.

### L1 Domain 5: Platform & Quality
- L2 Config & Packaging
- L2 Logging & Diagnostics
- L2 Automated Test Baseline
- L3 examples: user/local config precedence, structured local logs, deterministic unit tests.

For each L1/L2/L3 entry, include exactly these columns:
- `Capability ID`
- `Description`
- `Current Status` (`Implemented`/`Partial`/`Planned`)
- `Phase 1 Decision` (`Keep`/`Harden`/`Out`)
- `Acceptance Signal`

## Interaction Protocol (Decision-Complete)
Create `docs/interaction-protocol.md` as the normative protocol.

### 1. Actors
- User
- Overlay UI (`OverlayWindow`)
- Orchestrator (`main.py`)
- AI runtime (`AIAssistant`)
- Notification scheduler (`DailyChatSource` + loop)
- State store (`NotificationState`)

### 2. Canonical States
- `RESTING`, `GREETING`, `ALERT`, `AWAKE`, `THINKING`, `REPLY`, `IDLE_CHAT`

### 3. Canonical Events
- `ACTIVATE`, `SUBMIT`, `ANSWER`, `CHAT_ANSWER`, `DISMISS`, `AUTO_REST`
- `SLOT_DUE`, `SLOT_DELIVERED`, `SLOT_SKIPPED_NO_UNIQUE_TOPIC`
- `SLOT_DEFERRED_BUSY`, `SLOT_DRAINED`

### 4. Invariants (must hold)
1. At most one active interactive chat session at a time.
2. Proactive notifications are allowed only when `overlay.can_show_proactive()==True`.
3. Same-day proactive topic must not repeat across all slots.
4. Busy-at-slot-time behavior is defer, not interrupt.
5. Deferred slots are same-day only; no cross-day replay.
6. User language follows user input language.
7. Replies are concise and turn-by-turn by default.

### 5. Flow A: Manual Activation Flow
1. Trigger `ACTIVATE` via hotkey/click.
2. If onboarding required, show onboarding notice and stop flow.
3. Acquire activation lock.
4. Check wake-first slot eligibility.
5. If wake-first deliverable exists and UI safe, show proactive greeting and end activation flow.
6. Else capture last active window, detect app type, filter image, clear chat history, show ask UI.

### 6. Flow B: Ask/Reply Flow
1. User submits question (`SUBMIT`).
2. Orchestrator composes app-context question and optional image.
3. AI executes model call and optional `web_search` tool round-trip.
4. On answer, transition to `REPLY` or `IDLE_CHAT` per interaction mode.
5. If no further user input, auto return to `RESTING` on timeout.

### 7. Flow C: Scheduled Proactive Flow
1. Scheduler polls every fixed interval.
2. If daily chat disabled, skip cycle.
3. If UI not safe for proactive, emit `SLOT_DEFERRED_BUSY`, keep pending.
4. For pending due slots, generate slot content with dedupe retries.
5. If unique topic generated, persist slot delivered and show greeting.
6. If no unique topic after retries, persist skipped status and do not notify.

### 8. Flow D: Deferred Drain Flow
1. On later cycle when UI becomes safe, process oldest pending due slot first.
2. Deliver at most one slot per cycle.
3. Mark as delivered or skipped immediately after generation result.

### 9. Failure and Fallback Rules
- Generation failure logs reason and keeps behavior non-disruptive.
- JSON parse failure in daily topic generation retries within configured retry bound.
- Unexpected exceptions never break UI loop; they log and continue next cycle.

### 10. Structured Local Logging Schema
Use key-value structured log lines for protocol observability:
- Required fields: `event`, `flow`, `slot_id`, `pet_state`, `result`, `reason`, `date`, `time_local`.
- No remote telemetry in Phase 1.

## MVP Definition (Phase 1 Internal Alpha)
Create `docs/mvp-phase1.md` with this frozen scope.

### In Scope
1. Publish the three docs (`capability-map`, `interaction-protocol`, `mvp-phase1`).
2. Add targeted automated unit tests with pytest for:
- Daily slot due logic.
- Same-day dedupe logic.
- Skip-on-no-unique-topic behavior.
- Proactive delivery guard behavior.
- Pet transition invariants.
- Prompt policy string constraints for concise turn-by-turn guidance.
3. Add local structured protocol log events in existing runtime paths (no remote sink).
4. Keep existing behavior stable; no regression in current daily news functionality.

### Out of Scope
1. Observer/Assist/Execute permission-mode implementation.
2. Work-critical notification source integrations (email/slack/calendar).
3. Memory management UI (view/edit/reset).
4. Remote telemetry pipeline.
5. Cross-platform parity work (stay Windows-first).

## File-Level Implementation Plan
1. Add `docs/capability-map.md`.
2. Add `docs/interaction-protocol.md`.
3. Add `docs/mvp-phase1.md`.
4. Update `docs/soul-roadmap.md` to reference these new docs and Phase 1 completion gates.
5. Add `requirements-dev.txt` with pytest dependency.
6. Add `tests/unit/test_daily_chat_source.py`.
7. Add `tests/unit/test_protocol_invariants.py`.
8. Add `tests/unit/test_prompt_policy.py`.
9. Add minimal helper fixtures in `tests/conftest.py`.
10. Add structured log calls in existing paths:
- `main.py` scheduler/activation checkpoints.
- `src/notifications/daily_chat.py` slot generation outcomes.

## Test Cases and Scenarios
1. `test_slot_due_after_time_boundary`
- Given `15:00` slot and local time before/after boundary, pending logic matches expectation.
2. `test_same_day_topic_dedupe_across_slots`
- Given topic used by wake-first, 15:00/20:00 generation rejects duplicate topic key.
3. `test_skip_when_no_unique_topic_after_retry`
- Mock repeated duplicate topic and verify `skipped_no_unique_topic`.
4. `test_deferred_when_overlay_not_resting`
- Mock non-RESTING state and verify no proactive show call.
5. `test_deferred_drains_when_resting_again`
- Simulate busy then RESTING and verify same-day deferred slot is delivered once.
6. `test_pet_transition_invariants`
- Validate valid/invalid transitions against transition map.
7. `test_prompt_policy_contains_concise_turn_by_turn_rules`
- Validate prompt includes concise, turn-by-turn, and language-following constraints.
8. `test_no_cross_day_replay`
- Verify previous-day pending slots do not replay on next day.
9. `test_structured_log_fields_present`
- Capture logs and verify required keys are emitted for protocol events.

## Acceptance Criteria
1. All new docs exist and are internally consistent with `Soul.md`.
2. Pytest suite for new unit tests passes locally.
3. Existing runtime behavior for daily proactive news remains intact.
4. Logs include required protocol fields at key transitions.
5. No new runtime config required for end users.
6. All new/updated documentation and code remain English-only.

## Assumptions and Defaults
1. Platform target is Windows desktop for Phase 1.
2. System local timezone is trusted.
3. Notification scheduler runs only while app process is alive.
4. Legacy manual script tests under `tests/` remain for now and are not migrated in Phase 1.
5. Chinese can be used in team discussion, but committed docs/code stay English.
