# Soul Alignment Roadmap

This roadmap tracks implementation work required to align the product with `Soul.md`.

## Scope

- Product behavior boundaries
- Permission and execution controls
- Proactive notification policy
- Memory transparency and control
- Communication quality controls

## Status Legend

- `Done`: shipped in current codebase
- `In Progress`: partially implemented, needs hardening
- `Planned`: not implemented yet

## Current Baseline (Phase 1)

1. `Done` - Scheduled daily news pushes at first wake-up, 15:00, and 20:00.
2. `Done` - Same-day topic dedupe across all daily news slots.
3. `Done` - Catch-up behavior for scheduled slots when the UI becomes available on the same day.
4. `In Progress` - Concise turn-by-turn response style and technical co-worker prompt alignment.
5. `In Progress` - Focus-safe proactive gating (basic state check exists, richer policy still missing).

## Phase 2 - Soul Policy Hardening

1. `Planned` - Add prompt behavior test cases for creative-boundary compliance.
2. `Planned` - Add regression tests for concise response and one-step interaction flow.
3. `Planned` - Add policy checks for risk explanation and safer-alternative responses.

## Phase 3 - Permission Model

1. `Planned` - Introduce explicit collaboration modes: Observer, Assist, Execute.
2. `Planned` - Add task-scoped permission grants with expiration.
3. `Planned` - Add pre-execution action preview and user confirmation for Execute mode.

## Phase 4 - Proactive Intelligence

1. `Planned` - Add work-critical notification channel (email/slack/calendar signal ingestion).
2. `Planned` - Add urgency ranking and deferrable notification controls.
3. `Planned` - Add stronger focus detection to suppress non-urgent proactive output.

## Phase 5 - Memory Transparency

1. `Planned` - Define memory classes (session context vs preference abstraction).
2. `Planned` - Add user controls to view, edit, and reset stored preference memory.
3. `Planned` - Add strict exclusion for sensitive raw artifacts and private content.

## Phase 6 - Release Governance

1. `Planned` - Add a Soul-alignment checklist to release validation.
2. `Planned` - Require explicit review for changes touching boundaries in `Soul.md`.
3. `Planned` - Add changelog tags linking features to Soul principles.
