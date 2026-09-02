# Repository Quality Contract

These are Quant Brief's golden principles: a small set of invariants that future
agents can discover quickly and that automation can enforce wherever possible.

| Principle | Mechanical feedback | Repair direction |
|---|---|---|
| Dependencies follow `ARCHITECTURE.md` | `scripts/check-repository.py` parses imports | Move orchestration upward or declare a deliberate new module edge in both places |
| Every product module has one named responsibility | The checker rejects undeclared `quantbrief/*.py` files | Name the capability, document its interface, and add an explicit dependency rule |
| Modules remain navigable | Product modules are limited to 400 physical lines | Extract a cohesive deep module; do not scatter pass-through helpers |
| Repository-root files are deliberate | The checker rejects unapproved, non-ignored root files | Move the file to its owner from `AGENTS.md` or explicitly document a true project entry point |
| External shapes are normalized at their seam | Source, summary, Pipeline, and web tests cover accepted shapes | Parse into a canonical model before business logic uses the value |
| Knowledge Cards remain traceable | Pipeline tests require source identity and original links | Reject the Card or preserve its missing provenance at ingestion |
| Runtime state never becomes source | `.gitignore` and placement rules isolate `storage/` | Move the artifact under its canonical ignored runtime path |
| One command reproduces the feedback loop | `scripts/verify-change.ps1` runs repository, Python, and web checks | Fix the first reported invariant, rerun, then continue |

## Verification levels

- Fast Python feedback: `python -m unittest discover -s tests -v`
- Architecture feedback: `python scripts/check-repository.py`
- Complete local feedback: `./scripts/verify-change.ps1`
- Production-like Edition feedback: run `./scripts/run-local.ps1` only when the change
  affects live collection or summarization and suitable credentials are available.

Tests should cross the same interface as callers. Prefer observable results from
`Pipeline.run(...)`, `CardArchive`, `CandidatePool`, source adapters, and summarizer
adapters over assertions against private helpers.

## Continuous garbage collection

When review finds a repeating defect, repair the development environment as part of
the fix:

1. State the durable rule here, in `AGENTS.md`, or in `CONTEXT.md`.
2. Encode it in `scripts/check-repository.py` or a behavior test when it can be
   checked without human judgment.
3. Make the failure message name the repair path.
4. Remove obsolete rules when the architecture changes; stale guidance is itself a
   defect.

Human judgment remains necessary for editorial quality, source trust, and whether a
new seam earns its complexity. Automation protects the decisions after they are made.

## Current evidence and debt

[`docs/technical-debt.md`](technical-debt.md) records the evidence-based Quality
score, concrete technical debt, and repair triggers. Update the affected score row in
the same change that materially changes its evidence or largest gap. Executable work
belongs in an active execution plan, not only in the debt table.
