# BuddyGPT Capability Map

Phase 1 Internal Alpha — aligned with `Soul.md` and `phase1-product-blueprint.md`.

Status legend:
- **Implemented**: behavior exists in current product.
- **Partial**: behavior exists but is not complete or not fully enforced.
- **Planned**: behavior is a target, not implemented yet.

Phase 1 decision legend:
- **Keep**: no changes needed for Phase 1.
- **Harden**: needs tests, docs, or guardrails in Phase 1.
- **Out**: deferred beyond Phase 1.

---

## L1 Domain 1: Core Chat Experience

| Capability ID | Description | Current Status | Phase 1 Decision | Acceptance Signal |
|---|---|---|---|---|
| 1.1 App Activation | Hotkey/click triggers overlay with active-window context | Implemented | Keep | Hotkey wakes Shiba, captures correct window |
| 1.1.1 Hotkey activation | Configurable hotkey triggers `on_activate()` | Implemented | Keep | `HotkeyManager` routes activation correctly |
| 1.1.2 Mouse activation | Overlay click calls `on_activate` callback | Implemented | Keep | Click on resting Shiba opens ask UI |
| 1.2 Context Capture | Active-window screenshot + app detection + content filtering | Implemented | Keep | Screenshot captured, app type detected, PII filtered |
| 1.2.1 Active-window capture | `capture_window()` grabs target window pixels | Implemented | Keep | Image bytes non-empty for foreground window |
| 1.2.2 App-type detection | `detect_app()` identifies app category from process/title | Implemented | Keep | Known apps return correct `AppInfo` |
| 1.2.3 Content filtering | `filter_content()` masks sensitive regions | Implemented | Keep | Filtered image omits configured regions |
| 1.3 Response Generation | AI model call with app-context prompt + optional image | Implemented | Keep | Model returns relevant answer within token limit |
| 1.3.1 App-aware prompt merge | `build_context_prompt()` prepends app context to question | Implemented | Keep | Context prefix matches active app type |
| 1.3.2 Tool-call loop | `web_search` tool available for time-sensitive queries | Implemented | Keep | Search results integrated into answer |
| 1.4 Follow-up Session | Multi-turn conversation within one activation | Implemented | Keep | Subsequent questions reference prior answers |
| 1.4.1 Auto-rest | Overlay returns to RESTING on dismiss or timeout | Implemented | Keep | Pet state returns to RESTING after Esc/timeout |

## L1 Domain 2: Proactive Intelligence

| Capability ID | Description | Current Status | Phase 1 Decision | Acceptance Signal |
|---|---|---|---|---|
| 2.1 Daily News Scheduler | Three time slots deliver proactive news greetings | Implemented | Harden | Unit tests pass for slot-due logic |
| 2.1.1 Wake-first slot | First activation each day triggers news greeting | Implemented | Harden | `should_trigger_slot(wake_first)` returns True once per day |
| 2.1.2 Afternoon 15:00 slot | Scheduled push after 15:00 local time | Implemented | Harden | `pending_timed_slots()` includes slot after boundary |
| 2.1.3 Evening 20:00 slot | Scheduled push after 20:00 local time | Implemented | Harden | `pending_timed_slots()` includes slot after boundary |
| 2.2 Slot Deduplication | Same topic cannot repeat across slots on the same day | Implemented | Harden | Unit tests pass for same-day topic dedupe |
| 2.2.1 Topic normalization | `_normalize_topic()` lowercases and strips punctuation | Implemented | Keep | Equivalent topics collapse to same key |
| 2.2.2 Retry on duplicate | Generation retries up to `max_topic_retry` times | Implemented | Harden | Exhausted retries produce `skipped_no_unique_topic` |
| 2.3 Safe Delivery Gate | Proactive display only when UI is in RESTING state | Implemented | Harden | Unit tests pass for proactive guard behavior |
| 2.3.1 RESTING-only proactive | `can_show_proactive()` gates scheduled delivery | Implemented | Harden | Delivery blocked when pet is not RESTING |
| 2.3.2 Same-day catch-up drain | Deferred slots delivered when pet returns to RESTING | Implemented | Harden | Deferred slot delivered on next safe cycle |
| 2.3.3 No cross-day replay | Yesterday's pending slots do not carry to today | Implemented | Harden | New day resets slot availability |

## L1 Domain 3: Safety & Permission Governance

| Capability ID | Description | Current Status | Phase 1 Decision | Acceptance Signal |
|---|---|---|---|---|
| 3.1 Advice-First Prompt Policy | System prompt enforces analysis-first, no implicit actions | Partial | Harden | Prompt policy tests pass for key phrases |
| 3.1.1 Concise turn-by-turn | Prompt requires short, focused responses | Implemented | Harden | `SYSTEM_PROMPT` contains concise/turn-by-turn rules |
| 3.1.2 Language-following | Response matches user input language | Implemented | Harden | `SYSTEM_PROMPT` contains "same language" rule |
| 3.2 Execution Boundary | No implicit system-changing actions without explicit request | Partial | Keep | Prompt contains autonomous execution guard |
| 3.2.1 No autonomous execution | Prompt warns against unsolicited system changes | Partial | Harden | Prompt policy test validates execution boundary |
| 3.3 Risk Explanation Policy | Technical risks explained with safer alternatives offered | Partial | Keep | Prompt directs risk-aware responses |
| 3.3.1 Safety-first wording | Prompt avoids subjective judgments on creative work | Partial | Harden | Prompt policy test validates creative boundary |

## L1 Domain 4: Memory & Personalization

| Capability ID | Description | Current Status | Phase 1 Decision | Acceptance Signal |
|---|---|---|---|---|
| 4.1 Session Memory | In-session conversation history maintained | Implemented | Keep | Follow-up questions reference earlier context |
| 4.1.1 In-session history | `AIAssistant.history` tracks conversation turns | Implemented | Keep | Multi-turn dialogue works within one session |
| 4.2 Reset Semantics | History cleared at controlled activation points | Implemented | Keep | New activation clears prior conversation |
| 4.2.1 Activation reset | `ai.clear_history()` called on each new activation | Implemented | Keep | Fresh activation starts clean context |
| 4.3 Privacy Boundary | No broad background indexing or raw artifact storage | Implemented | Keep | No persistent storage of screenshots or responses |
| 4.3.1 No background indexing | App only captures on explicit activation | Implemented | Keep | No background screenshot collection |

## L1 Domain 5: Platform & Quality

| Capability ID | Description | Current Status | Phase 1 Decision | Acceptance Signal |
|---|---|---|---|---|
| 5.1 Config & Packaging | User/local config with sensible defaults | Implemented | Keep | `load_config()` merges user overrides correctly |
| 5.1.1 User config precedence | `config.json` and `.env` override defaults | Implemented | Keep | Custom values take effect after restart |
| 5.1.2 Notification config | `daily_chat` settings in config control scheduler | Implemented | Keep | `enabled: false` disables daily chat |
| 5.2 Logging & Diagnostics | Structured local logs for protocol observability | Partial | Harden | Key protocol events logged with slot identification |
| 5.2.1 Structured local logs | Log lines include event, slot, and state context | Partial | Harden | Log capture tests verify field presence |
| 5.3 Automated Test Baseline | Deterministic unit tests for critical paths | Implemented | Harden | `pytest tests/unit/ -v` passes all 9 cases |
| 5.3.1 Slot scheduling tests | Tests 1-4: slot-due, dedupe, skip, cross-day | Implemented | Harden | 4 test classes pass |
| 5.3.2 Protocol invariant tests | Tests 5-7: transitions, guard, drain | Implemented | Harden | 3 test classes pass |
| 5.3.3 Prompt policy tests | Tests 8-9: policy phrases, log fields | Implemented | Harden | 2 test classes pass |
