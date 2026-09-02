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
- [ ] Add the R2 adapter, binding configuration, credential scopes, and preview bucket.
- [ ] Add website date routing and historical navigation against the public index.
- [ ] Route both scheduled and operator publication through the shared interface.
- [ ] Run a preview publish, idempotent re-publish, injected partial failure, and restore
  drill; retain their receipts.
- [ ] Cut production reads over while retaining the latest-JSON fallback.

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

## Verification

Planning baseline on 2026-09-02:

- `python scripts/check-repository.py` — passed.
- `python -m unittest discover -s tests -v` — 49 tests passed.
- `pnpm test`, `pnpm lint`, and `pnpm build` through
  `./scripts/verify-change.ps1` with `CI=true` — 5 web tests, lint, and production build
  passed.

Implementation verification and preview publication receipts will be appended here.

## Outcome

Pending implementation. Move this plan to `docs/exec-plans/completed/` only after all
acceptance criteria pass and the production cutover or an explicit stop decision is
recorded.
