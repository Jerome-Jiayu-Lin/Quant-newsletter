# Technical debt tracker

Debt entries name a concrete gap and trigger. Work ready to execute belongs in an
active execution plan instead. The accepted public-platform direction is recorded in
[`ADR-0001`](adr/0001-separate-public-content-and-reader-state.md); its first
executable increment is tracked in
[`publish-historical-editions.md`](exec-plans/active/publish-historical-editions.md).

| ID | Area | Debt | Trigger to address |
|---|---|---|---|
| TD-001 | Publication coordination | The scheduled GitHub workflow writes the latest `web/data/cards.json` directly, while the operator publication script validates a local Edition Snapshot, commits the same compatibility file from a temporary checkout, and separately deploys the Worker. These paths do not share one publication interface or one durable receipt. | while implementing the active historical-publication plan; retire direct workflow writes only after the shared publisher proves compatibility and rollback |
| TD-002 | Reader identity | Clerk is the accepted public-reader identity provider, but no token-verification adapter, stable subject mapping, session failure behavior, or provider-exit test exists. | after anonymous historical browsing is deployed and an explicit product decision enables public accounts; complete before accepting the first authenticated request |
| TD-003 | Reader state | D1 is the accepted owner for Favorites and future reader-scoped preferences, but no schema, migration discipline, authorization policy, deletion behavior, or backup/export path exists. | in the same execution plan that introduces the first Favorite; require a stable Card identifier and authenticated-reader contract first |
| TD-004 | Administration | Cloudflare Access is the accepted administrative identity boundary, but there is no administrative surface, Access policy, role model, mutation audit record, or recovery procedure. | before exposing the first remote administrative mutation; keep publication operator-only until the complete boundary is enforced and tested |
| TD-005 | Public-platform security | The future Worker API has no threat model, request authorization matrix, rate limits, CSRF decision, security headers contract, or adversarial tests because no public mutation API exists yet. | before provisioning a production D1 binding or enabling any browser-originated mutation |
| TD-006 | Operational evidence | Repository tests prove deterministic local behavior, but publication does not retain a machine-readable receipt binding Edition identity, export hash, object keys, deployment identifier, and rollback result. | implement with the shared R2 publisher before production cutover; require one observed publish and one restore drill before raising Publication or Reliability above C |

Resolved: no debt entries have been closed in this tracker yet. When one is closed,
move it below this sentence with the closure date, delivered enforcement, tests, and
any deliberately retained compatibility behavior.

# Quality score

Grades describe current repository evidence, not intended architecture. A row must be
updated in the same change that materially alters its evidence or largest gap.

| Area | Grade | Evidence | Largest gap |
|---|---:|---|---|
| Knowledge plane | B | canonical domain language, architecture map, quality contract, ADR, technical-debt tracker, execution-plan lifecycle, and repository checks for required knowledge files and module ownership | document freshness is enforced only by review and file presence, not semantic drift checks |
| Architecture | B | explicit Python dependency direction, runtime ownership, public-platform boundaries, AST dependency lint, root placement enforcement, and repair-oriented checker tests | the accepted public-platform adapters have not been implemented or exercised together |
| Collection and editorial pipeline | B | source seams, canonical models, ranking and Candidate Pool rules, strict bilingual summarization, traceability checks, 49 Python tests, and a scheduled production-shaped workflow | no retained end-to-end Edition receipt demonstrates a complete live run from source fetch through publication |
| Local persistence | B | canonical dated Edition Snapshots, idempotent SQLite Archive ingestion, historical Git synchronization, date-plus-Feature search, and behavior tests | backup restoration and corruption recovery are documented only indirectly and have no drill evidence |
| Website | B | validated remote-Edition fallback, bilingual rendering contract, five data-loader tests, lint, and production build verification | no browser-level route, accessibility, or failure-state test exercises the deployed site |
| Publication | C | Edition completeness validation, clean temporary-checkout publication, scheduled latest-Edition commits, Worker deployment, and build-before-publish behavior | two publication paths diverge, only the latest Edition is public, and no durable publication receipt or rollback drill exists |
| Historical delivery | D | R2 ownership, dated Public Export shape, compatibility migration, and ordering constraints are decided in ADR-0001 and the active execution plan | no R2 bucket binding, history index, dated public object, migration test, or deployed historical route exists |
| Reader identity and state | D | Clerk and D1 responsibilities are separated from editorial authority in ADR-0001 | no account, token verification, Favorite schema, authorization test, export, or deletion behavior exists |
| Administration | D | Cloudflare Access is selected as the independent administrative identity boundary | no protected admin surface, role policy, audited mutation, or recovery procedure exists |
| Reliability | C | source fetch state, Candidate Pool persistence, idempotent Edition reruns, strict publication validation, CI checks, and remote-data fallback are implemented | publication recovery, retained receipts, remote object consistency, and real interruption behavior are untested |
| Security | C | secrets stay outside Public Exports, CI uses scoped tokens, local runtime artifacts are ignored, browser code has no database credential, and provenance is mandatory | the future identity and mutation boundaries have no executable authorization or abuse-resistance evidence |

## Grade meaning

- **A** — enforced, adversarially tested, and observed in a real production publication or recovery run.
- **B** — enforced and tested, but not yet proven by the relevant complete production run.
- **C** — interface and acceptance behavior are precise; enforcement or operational evidence is partial.
- **D** — intent is documented but the executable capability is absent.
- **F** — unknown, contradictory, or known unsafe.
