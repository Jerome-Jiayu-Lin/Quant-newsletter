# Technical debt tracker

Debt entries name a concrete gap and trigger. Work ready to execute belongs in an
active execution plan instead. The accepted public-platform direction is recorded in
[`ADR-0001`](adr/0001-separate-public-content-and-reader-state.md); its first
executable increment is tracked in
[`publish-historical-editions.md`](exec-plans/active/publish-historical-editions.md).

| ID | Area | Debt | Trigger to address |
|---|---|---|---|
| TD-001 | Publication coordination | The scheduled workflow and operator command now share `quantbrief.publish_cli`, but the compatibility Git commit and Worker deployment remain operator-specific until the R2 preview and rollback drills prove cutover safety. | retire the remaining compatibility path only after preview publication, restore, and deployed-read evidence |
| TD-002 | Reader identity | Clerk is the accepted public-reader identity provider, but no token-verification adapter, stable subject mapping, session failure behavior, or provider-exit test exists. | after anonymous historical browsing is deployed and an explicit product decision enables public accounts; complete before accepting the first authenticated request |
| TD-003 | Reader state | D1 is the accepted owner for Favorites and future reader-scoped preferences, but no schema, migration discipline, authorization policy, deletion behavior, or backup/export path exists. | in the same execution plan that introduces the first Favorite; require a stable Card identifier and authenticated-reader contract first |
| TD-004 | Administration | Cloudflare Access is the accepted administrative identity boundary, but there is no administrative surface, Access policy, role model, mutation audit record, or recovery procedure. | before exposing the first remote administrative mutation; keep publication operator-only until the complete boundary is enforced and tested |
| TD-005 | Public-platform security | The future Worker API has no threat model, request authorization matrix, rate limits, CSRF decision, security headers contract, or adversarial tests because no public mutation API exists yet. | before provisioning a production D1 binding or enabling any browser-originated mutation |

Resolved:

- **TD-006 — 2026-09-02.** The shared publisher now retains immutable,
  machine-readable publication receipts and verified recovery objects. A real
  `jerome-brief-preview` run recorded published, unchanged, changed, stale-writer
  rejection, and restored outcomes; the final index hash matched the verified
  baseline. The Git compatibility export remains deliberately retained until a
  deployed R2-backed read is observed.

# Quality score

Grades describe current repository evidence, not intended architecture. A row must be
updated in the same change that materially alters its evidence or largest gap.

| Area | Grade | Evidence | Largest gap |
|---|---:|---|---|
| Knowledge plane | B | canonical domain language, architecture map, quality contract, ADR, technical-debt tracker, execution-plan lifecycle, and repository checks for required knowledge files and module ownership | document freshness is enforced only by review and file presence, not semantic drift checks |
| Architecture | B | explicit dependency direction, runtime ownership, public-platform boundaries, a provider-independent publisher, a tested conditional R2 adapter, a real preview-bucket recovery drill, and repair-oriented repository checks | the public route has not yet been observed reading R2 in a deployed environment |
| Collection and editorial pipeline | B | source seams, canonical models, ranking and Candidate Pool rules, strict bilingual summarization, traceability checks, 49 Python tests, and a scheduled production-shaped workflow | no retained end-to-end Edition receipt demonstrates a complete live run from source fetch through publication |
| Local persistence | B | canonical dated Edition Snapshots, idempotent SQLite Archive ingestion, historical Git synchronization, date-plus-Feature search, and behavior tests | backup restoration and corruption recovery are documented only indirectly and have no drill evidence |
| Website | B | indexed R2 latest reads with two-stage compatibility fallback, bilingual rendering, localized historical Edition/Card routes, explicit missing/unavailable states, ten data-loader tests, lint, and production build verification | no browser-level accessibility or failure-state test exercises a deployed R2-backed route |
| Publication | B | Scheduled and operator flows share one tested CLI for completeness validation, conditional R2 publication, receipt retention, and post-success compatibility export; a real preview run proved idempotency, conflict rejection, and rollback | compatibility Git/deploy orchestration remains intentionally separate until a deployed R2-backed read is observed |
| Historical delivery | C | production and preview R2 buckets exist; the preview bucket contains a verified Edition, index, receipts, and recovery snapshots alongside indexed website loaders and compatibility fallbacks | no deployed website read from the real R2 binding has been observed |
| Reader identity and state | D | Clerk and D1 responsibilities are separated from editorial authority in ADR-0001 | no account, token verification, Favorite schema, authorization test, export, or deletion behavior exists |
| Administration | D | Cloudflare Access is selected as the independent administrative identity boundary | no protected admin surface, role policy, audited mutation, or recovery procedure exists |
| Reliability | B | source fetch state, idempotent Edition reruns, conditional publication, immutable recovery objects, verified restore command, fake-storage failure tests, a successful real preview restore drill, CI checks, and remote-data fallback are implemented | production publication and deployed-reader recovery have not yet been exercised |
| Security | C | secrets stay outside Public Exports, CI uses scoped tokens, local runtime artifacts are ignored, browser code has no database credential, and provenance is mandatory | the future identity and mutation boundaries have no executable authorization or abuse-resistance evidence |

## Grade meaning

- **A** — enforced, adversarially tested, and observed in a real production publication or recovery run.
- **B** — enforced and tested, but not yet proven by the relevant complete production run.
- **C** — interface and acceptance behavior are precise; enforcement or operational evidence is partial.
- **D** — intent is documented but the executable capability is absent.
- **F** — unknown, contradictory, or known unsafe.
