# BuddyGPT MVP Phase 1 — Internal Alpha

Frozen scope definition for the Phase 1 Internal Alpha release.

---

## Release Audience

Internal alpha: developer testing and validation only.

---

## In Scope

### 1. Documentation

Publish three authoritative specification documents:

- `docs/capability-map.md` — 5-domain capability map (L1/L2/L3) with status and acceptance signals.
- `docs/interaction-protocol.md` — Normative interaction protocol: states, events, invariants, flows, failure rules, logging schema.
- `docs/mvp-phase1.md` — This document. Frozen MVP scope for Phase 1.

### 2. Automated Unit Tests

Targeted deterministic test suite using `pytest`. No API calls, no network access.

| Test ID | File | Description |
|---|---|---|
| 1 | `test_daily_chat_source.py` | Slot due after time boundary |
| 2 | `test_daily_chat_source.py` | Same-day topic dedupe across slots |
| 3 | `test_daily_chat_source.py` | Skip when no unique topic after retries |
| 4 | `test_daily_chat_source.py` | No cross-day replay of delivered slots |
| 5 | `test_protocol_invariants.py` | Pet state transition invariants (valid + invalid) |
| 6 | `test_protocol_invariants.py` | Proactive delivery blocked when not RESTING |
| 7 | `test_protocol_invariants.py` | Deferred slot drains when pet returns to RESTING |
| 8 | `test_prompt_policy.py` | System prompt contains required policy phrases |
| 9 | `test_prompt_policy.py` | Structured log fields present in slot generation |

Dev dependency: `requirements-dev.txt` with `pytest>=8`.
Shared fixtures: `tests/conftest.py` (FakeAI, fake_state, daily_source, default_config).

### 3. Local Structured Logging

Key protocol events produce log output with identifiable fields:
- Slot identification in generation and skip paths.
- Exception logging with context in scheduler and activation flows.
- No remote telemetry pipeline in Phase 1.

### 4. Runtime Stability

- Existing daily proactive news functionality remains stable.
- No regression in core chat experience (activation, context capture, response generation).
- No new runtime config required for end users.
- Config format unchanged.

---

## Out of Scope

The following items are explicitly deferred beyond Phase 1:

### 1. Permission Mode Implementation
Observer/Assist/Execute collaboration modes defined in `Soul.md` Section 4.
Requires deeper execution policy controls and task-bounded permission tracking.

### 2. Work-Critical Notification Sources
- Email integration with AI-powered smart filtering
- Slack integration with urgency detection
- Google Calendar meeting reminders with pre-meeting context

These require OAuth flows, third-party API integration, and more complex scheduling.

### 3. Memory Management UI
User-visible memory controls (view, edit, reset) for policy-level memory.
Currently session memory is managed internally with activation-point resets.

### 4. Remote Telemetry
No remote logging, metrics collection, or analytics pipeline.
Phase 1 uses local `logging` module output only.

### 5. Cross-Platform Parity
BuddyGPT targets Windows desktop exclusively in Phase 1.
macOS and Linux support are not in scope.

---

## Acceptance Criteria

1. All three documentation files exist and are internally consistent with `Soul.md`.
2. `pytest tests/unit/ -v` passes all 9 test cases locally.
3. Existing runtime behavior for daily proactive news remains intact.
4. Logs include slot identification at key protocol transitions.
5. No new runtime config required for end users.
6. All new and updated documentation and code are English-only.

---

## Verification Command

```bash
pip install -r requirements-dev.txt
pytest tests/unit/ -v
```

All 9 tests should pass. No existing functionality should break.

---

## Assumptions

1. Platform target is Windows desktop.
2. System local timezone is trusted for slot scheduling.
3. Notification scheduler runs only while the app process is alive.
4. Legacy manual test scripts under `tests/` remain and are not migrated in Phase 1.
5. Chinese can be used in team discussion, but committed docs and code stay English.
