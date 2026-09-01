# Implement <Capability and Outcome>

## Purpose

Explain the user-visible outcome and why this work is necessary.

## Acceptance criteria

- [ ] State observable behavior, not implementation activity.
- [ ] Include compatibility, data, and failure expectations where relevant.
- [ ] Name the verification evidence required for completion.

## Architecture

Describe the affected modules, interfaces, seams, dependency direction, persisted
state, and rollback path. Link to `ARCHITECTURE.md` instead of copying its rules.

## Progress

- [ ] Record the current next action.

## Discoveries

Capture facts that changed the plan, with file paths or command output sufficient for
another agent to verify them.

## Decision log

Record each non-obvious choice, alternatives considered, and why the choice preserves
the repository's invariants.

## Verification

List the exact commands run and their results. The minimum handoff check is
`./scripts/verify-change.ps1` unless the plan explains why a narrower check is valid.

## Outcome

Complete this section when moving the plan to `completed/`: summarize delivered
behavior, remaining debt, and any follow-up that is intentionally out of scope.
