# Publish historical Editions through one durable public path

## Purpose

Make every published Singapore-date Edition addressable on the website while keeping
the private Archive local. Replace the two current publication paths with one tested,
idempotent publication interface that writes sanitized dated Public Exports and a
history index to Cloudflare R2, retains the latest `web/data/cards.json` compatibility
contract during migration, and emits enough evidence to restore a previous publication.

## Acceptance criteria

- [ ] Publishing Edition `YYYY-MM-DD` writes exactly one sanitized dated Public Export
  at a deterministic key and makes the date discoverable through a versioned history
  index without exposing Archive-only or runtime fields.
- [ ] Re-publishing the same unchanged Edition is idempotent; publishing a changed
  canonical snapshot updates that date deliberately and records the previous and new
  content hashes.
- [ ] Data objects are uploaded and verified before the history index is replaced, so
  an index never advertises a missing or unverified Edition.
- [ ] The website can render the latest Edition and a requested historical date, with
  explicit not-found and temporarily-unavailable behavior.
- [ ] `web/data/cards.json` remains a validated fallback during migration, and its
  removal requires a later explicit compatibility decision.
- [ ] The scheduled workflow and operator command invoke the same publication
  interface; neither duplicates validation, key construction, or remote writes.
- [ ] Every publish emits a retained machine-readable receipt containing Edition date,
  canonical snapshot hash, public export hash, object keys, prior index hash, resulting
  index hash, deployment identifier when available, and outcome.
- [ ] A documented restore command can repoint the history index to the last verified
  state without modifying the private Archive; one non-production restore drill is
  recorded before production cutover.
- [ ] Unit and integration tests cover sanitization, deterministic keys, idempotency,
  upload-before-index ordering, partial failure, stale writer rejection, malformed
  remote data, and compatibility fallback.
- [ ] `./scripts/verify-change.ps1` passes, and the relevant rows and debts in
  `docs/technical-debt.md` are updated in the same change.

## Architecture

Follow the public-platform boundary in [`ARCHITECTURE.md`](../../../ARCHITECTURE.md)
and [`ADR-0001`](../../adr/0001-separate-public-content-and-reader-state.md).

The local Edition Snapshot remains the publication input, and `CardArchive` remains
the authority for rebuilding history. Introduce one publication interface above a
provider adapter: the core validates and serializes a Public Export, constructs dated
keys and the index, and returns a typed publication receipt; the Cloudflare adapter
performs R2 reads and conditional writes. The Pipeline, Knowledge Card model, and
Archive must not import Cloudflare clients.

The intended public layout is:

```text
editions/v1/index.json
editions/v1/YYYY/MM/YYYY-MM-DD/quant-brief-edition.json
publication-receipts/YYYY/MM/YYYY-MM-DD/<export-hash>.json
```

Receipts may be retained in an operator-controlled repository or object prefix, but
they must not expose credentials or private Archive fields. Browser reads use a
read-only public path. Publisher credentials remain server-side and write-scoped.

Rollback changes only the public index or restores a prior verified object version;
it never rewrites the local Edition Snapshot or Archive. D1, Clerk, Favorites, and the
administrative UI are explicitly out of scope for this plan.

## Progress

- [x] Record the accepted storage and identity boundary in ADR-0001.
- [x] Inventory the current GitHub Actions and operator publication paths.
- [x] Define the versioned Public Export index schema, publication receipt schema,
  stable Card identity rules, and sanitization allowlist.
- [x] Add the provider-independent publisher with fake-storage contract tests.
- [x] Add the R2 adapter, production/preview binding configuration, credential scopes,
  and reproducible bucket-provisioning procedure.
- [ ] Provision the real preview bucket and smoke-test its conditional writes; the
  current host has no Cloudflare login or R2 credentials.
- [x] Add website date routing and historical navigation against the public index.
- [x] Route both scheduled and operator publication through the shared interface.
- [ ] Run a preview publish, idempotent re-publish, injected partial failure, and restore
  drill; retain their receipts.
  - [x] Run the complete sequence against fake storage and retain its hashes below.
  - [ ] Repeat against the real preview R2 bucket after Cloudflare authorization exists.
- [x] Make the production loader prefer the indexed R2 latest Edition while retaining
  the validated latest-JSON and bundled fallbacks.
- [ ] Observe a deployed read from real R2 before removing migration status or moving
  this plan to completed.

## Discoveries

- `web/lib/cards.ts` currently fetches one no-store remote `cards.json` and falls back
  to the bundled copy after completeness validation.
- `.github/workflows/daily-brief.yml` writes `web/data/cards.json` directly to `main`;
  `scripts/publish-edition.ps1` independently validates, commits through a clean
  temporary checkout, and deploys the Worker.
- `web/wrangler.jsonc` currently declares routes and observability only; it has no R2
  or D1 binding.
- `CardArchive` can rebuild multiple Editions locally, so public cloud persistence does
  not need to become editorial authority.

## Decision log

- Start with R2 and static dated Public Exports. D1 is unnecessary for ordinary
  historical browsing and remains deferred until mutable reader state or server-side
  catalog queries exist.
- Keep a versioned index rather than listing bucket objects at request time. The index
  is a small public contract that can be cached, validated, and restored atomically.
- Upload and verify content before conditionally replacing the index. This prevents a
  visible index entry from pointing at an incomplete publication and rejects stale
  concurrent publishers.
- Keep the existing latest JSON as a temporary compatibility fallback. Removing it in
  the same migration would combine public-history delivery with an avoidable rollback
  risk.
- Version 1 contracts live in `quantbrief.publication`: sanitized exports use an
  explicit Card allowlist, dates normalize to ISO form, index entries are unique and
  newest-first, and receipts retain the hashes and keys needed for recovery.
- The provider-independent `Publisher` uses conditional object versions and verifies
  the dated Public Export before replacing the index. Fake-storage tests exercise
  first publish, unchanged and changed re-publish, verification failure, write order,
  receipt retention, and stale-index rejection without Cloudflare dependencies.
- `quantbrief.r2.R2ObjectStorage` adapts R2's S3 API without leaking provider details
  into the publisher. The Worker binding separates `jerome-brief-public` from
  `jerome-brief-preview`; `docs/operations/publish-to-r2.md` owns provisioning,
  bucket-scoped credential requirements, and conflict-handling guidance.
- Repository configuration was completed without provisioning cloud resources because
  the 2026-09-02 development host had no Wrangler login, Cloudflare API token, account
  identifier, or R2 S3 credentials. Do not treat the configured preview bucket name as
  evidence that the bucket exists.
- The website now discovers dates through `editions/v1/index.json`, renders localized
  Edition and Card routes under `/editions/YYYY-MM-DD`, preserves date context in Card
  links, and distinguishes an absent index entry from an advertised object that cannot
  be fetched or validated. Latest reads retain the bundled compatibility fallback.
- `quantbrief.publish_cli` now owns the complete bilingual publication gate, R2
  invocation, receipt output, and post-success compatibility export. The scheduled
  workflow and operator PowerShell script both invoke it instead of duplicating Card
  validation, key construction, or remote writes.
- Recovery does not rely on mutable dated objects or provider-specific version IDs.
  Publications retain content-addressed Edition versions and index snapshots;
  `quantbrief.restore_cli` verifies and restores them before conditionally repointing
  the active index, and can retain a machine-readable restore receipt locally.
- Latest website reads now resolve the index's `latestEdition` and use the same dated
  loader as historical routes. Invalid or unavailable R2 data falls through to the
  GitHub compatibility JSON and bundled Edition; an explicit historical date never
  substitutes fallback content from a different date.

## Verification

Planning baseline on 2026-09-02:

- `python scripts/check-repository.py` — passed.
- `python -m unittest discover -s tests -v` — 49 tests passed.
- `pnpm test`, `pnpm lint`, and `pnpm build` through
  `./scripts/verify-change.ps1` with `CI=true` — 5 web tests, lint, and production build
  passed.

Implementation verification and preview publication receipts will be appended here.

Historical-routing increment on 2026-09-02:

- `./scripts/verify-change.ps1` with `CI=true` — 66 Python tests, 8 web tests, lint,
  and production build passed.
- Local Vinext/Workers preview — root route returned HTTP 200 after aligning the
  configured compatibility date with the repository's locked Workers runtime.
- No preview R2 request was claimed: the host still lacks Cloudflare authorization.

Fake-storage recovery drill on 2026-09-02:

- Initial Public Export hash:
  `cb77c1a85fc7ca1ce59348254e377ab1e1fe8ea3be4880f947a53235e6d86633`.
- Initial index hash:
  `2a6ab81fa0f722944caa6da74706b5c9f372fde4c7295b60589acf27095e5656`.
- Unchanged re-publish outcome: `unchanged`.
- Changed publication index hash:
  `979107e0245daa19c6eca6b6438ce4bb763f2658dc67c7533e487d38e3c623bd`.
- Injected conditional-index failure: `StalePublicationError`; no receipt or index
  replacement was accepted for the failed candidate.
- Restore receipt outcome: `restored`, from prior index hash `979107e...23bd` to
  verified target `2a6ab8...5656`, deployment identifier `fake-drill:restore`.
- This is deterministic contract evidence, not a claim of real R2 operation.

## Outcome

Pending implementation. Move this plan to `docs/exec-plans/completed/` only after all
acceptance criteria pass and the production cutover or an explicit stop decision is
recorded.
