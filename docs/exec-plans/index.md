# Execution Plans for Long-Running Changes

Execution Plans keep complex work recoverable without relying on chat history. Use
one when a change spans multiple sessions, changes persisted data, crosses Python and
web paths, or has a rollback decision that a future agent must understand.

Small changes should use an ephemeral plan in the active task instead of creating a
document.

## Lifecycle

1. Copy `docs/exec-plans/template.md` to
   `docs/exec-plans/active/<descriptive-capability>.md`.
2. Record acceptance criteria before implementation.
3. Keep progress, discoveries, decisions, and verification evidence current while
   work proceeds.
4. Move the file to `docs/exec-plans/completed/` when every acceptance criterion is
   satisfied.
5. Delete abandoned plans only after preserving any durable architecture decision in
   `ARCHITECTURE.md` or a numbered ADR under `docs/adr/`.

Plan filenames describe the capability, not the agent, date, or ticket alone.
