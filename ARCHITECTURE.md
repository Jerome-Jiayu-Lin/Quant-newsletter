# Quant Brief Architecture

This document is the map for changing Quant Brief. Domain language lives in
[`CONTEXT.md`](CONTEXT.md), repository rules live in [`AGENTS.md`](AGENTS.md), and the
mechanically enforced quality contract lives in [`docs/QUALITY.md`](docs/QUALITY.md).

## System shape

Quant Brief has two deployable paths:

1. The Python collection path turns external source data into one traceable Edition.
2. The web path reads a public Edition export and renders the feed and detail pages.

The durable local Archive and Candidate Pool are runtime stores, not alternate entry
points. The website never reads either store directly.

The accepted public persistence and identity target is recorded in
[`ADR-0001`](docs/adr/0001-separate-public-content-and-reader-state.md). It is a
staged target, not a description of currently deployed infrastructure.

## Python module map

`Pipeline.run(...)` is the deep module interface for Edition construction. It hides
collection, normalization, deduplication, ranking, selection, summarization, feature
extraction, and serialization. Callers should not reproduce those steps.

Dependencies point downward in this table. A module may depend only on the modules
listed in its row; `scripts/check-repository.py` enforces the same graph.

| Module | Responsibility | Allowed internal dependencies |
|---|---|---|
| `__init__` | Stable package export for `Pipeline` and `PipelineReport` | `pipeline` |
| `models` | Canonical in-process Raw Item and Knowledge Card shapes | none |
| `http` | Conditional HTTP transport and fetch state | none |
| `features` | Stable Feature extraction | `models` |
| `ranking` | Content Section comparison and scoring | `models` |
| `candidates` | Candidate Pool persistence and publication memory | `models` |
| `sources` | External source adapters that produce Raw Items | `http`, `models` |
| `summarize` | Source, OpenAI, and DeepSeek summary adapters | `models` |
| `publication` | Provider-independent publication coordination and versioned public contracts | none |
| `r2` | Cloudflare R2 object-storage adapter and environment assembly | `publication` |
| `publish_cli` | Shared scheduled and operator publication entry point | `publication`, `r2` |
| `restore_cli` | Verified public-index recovery entry point and receipt writer | `publication`, `r2` |
| `pipeline` | Edition orchestration and public export creation | all modules above except `archive` |
| `archive` | Durable Edition ingestion and search | none |
| `archive_sync_cli` | Verified production R2 history synchronization into the local Archive | `archive`, `publication`, `r2` |
| `cli` | Collection entry point and dependency assembly | `pipeline`, `archive` |

The import direction is therefore:

```text
cli -> pipeline -> sources -> http
 |        |  \----> summarize
 |        \-------> candidates / features / ranking -> models
 \-> archive
```

## Seams and adapters

Only variability that exists in production or tests gets a seam:

- `SourceAdapter.fetch(...)` is the source seam. RSS, Hugging Face, GitHub, and
  GitHub Trending are adapters; test fakes use the same interface.
- `Summarizer.summarize(...)` is the summary seam. Source-only, OpenAI, DeepSeek,
  and test summarizers are adapters.
- `Pipeline.run(...)` is the external Edition-building interface. Its client,
  summarizer, ranker, and Feature extractor are accepted dependencies so tests can
  exercise the interface without network access.

Do not add a port for a dependency with only one implementation. Keep internal
helpers private until a second adapter or caller proves that a seam is real.

## Data flow and validation points

```text
config/sources.toml
  -> source adapters parse external responses into RawItem
  -> Pipeline canonicalizes and deduplicates identities
  -> CandidatePool separates fresh and carryover eligibility
  -> CohortRanker compares within Content Sections
  -> Pipeline enforces Edition coverage and caps
  -> summarizer adapter returns bilingual editorial fields
  -> KnowledgeCard.as_web_dict() creates the public shape
  -> web/lib/cards.ts accepts only a complete remote Edition
  -> UI renders the accepted public export
```

External data must be parsed at the first repository-owned seam. Downstream modules
operate on `RawItem`, `KnowledgeCard`, or the documented public export shape; they
must not probe third-party response dictionaries.

Website latest reads first resolve `latestEdition` through the versioned public index
and load that dated Public Export through the same validation path as historical
routes. During migration only, an unavailable or invalid indexed latest Edition falls
back to the validated GitHub latest JSON and then the bundled Edition. Historical
requests never silently substitute another date.

## Runtime ownership

| State | Owner | Canonical location |
|---|---|---|
| Fetch State | `HttpClient` | `storage/state/local-fetch-state.json` |
| Candidate Pool | `CandidatePool` | `storage/candidates/rolling-candidate-pool.json` |
| Edition Snapshot | `Pipeline` | `storage/editions/YYYY/MM/YYYY-MM-DD/quant-brief-edition.json` |
| Archive | `CardArchive` | `storage/archive/quant-brief.sqlite3` |
| Public Export | `Publisher` | versioned keys in Cloudflare R2 |

All `storage/` content is ignored. Re-running an Edition updates its canonical path
idempotently.

## Public platform target

The public platform separates published editorial content from mutable reader state.
No cloud service is authoritative for the private Archive or Candidate Pool.

```text
local Pipeline -> Edition Snapshot -> Public Export publisher -> R2
                                                        |          \
                                                        |           -> public website
                                                        v
                                                     D1 metadata

reader -> Clerk identity -> Worker API -> D1 reader state
editor -> Cloudflare Access -> admin UI -> Worker API -> publication workflow
```

The target responsibilities are:

| Capability | Owner | Authority and boundary |
|---|---|---|
| Complete private history | Local `CardArchive` | Remains the durable source for rebuilding public history; never exposed to the website |
| Published Edition documents | Cloudflare R2 | Stores dated, sanitized Public Exports and a replace-last history index; objects contain no reader state |
| Public catalog metadata | Cloudflare D1 | Stores only metadata needed for server-side listing, filtering, and publication status when static indexes stop being sufficient |
| Reader identity | Clerk | Authenticates public readers; Quant Brief stores only the stable external subject identifier needed to associate application state |
| Reader state | Cloudflare D1 | Stores favorites and future account-scoped preferences; it does not become an editorial Archive |
| Administrative identity | Cloudflare Access | Restricts the administrative surface independently of public reader authentication |
| Public and administrative APIs | Cloudflare Workers or Pages Functions | Verify identity, authorize each operation, and provide the only runtime path to D1 bindings |

Browser code must never receive D1 credentials or a write-capable R2 credential.
Clerk authentication proves reader identity but does not grant application
authorization by itself. Administrative publication continues to produce a validated
Public Export rather than allowing the website to read the private Archive directly.

Adopt this target incrementally:

1. Publish dated Public Exports plus a history index to R2; retain the bundled
   `web/data/cards.json` only as a static emergency fallback.
2. Add D1 only when server-side catalog queries, favorites, or other mutable public
   state are implemented. Static history browsing does not require D1.
3. Protect the first administrative surface with Cloudflare Access.
4. Add Clerk only when public reader accounts are implemented; anonymous reading
   remains independent of the identity provider.

Provider-specific code belongs at adapters on the publication or web runtime edges.
Knowledge Card and Edition construction must not import Cloudflare or Clerk clients.

The R2 provider edge is `quantbrief.r2.R2ObjectStorage`. It preserves R2 ETags as
conditional versions, creates objects with `If-None-Match`, and replaces them with
`If-Match`. Runtime credentials are bucket-scoped and server-side. The website's
`PUBLIC_EDITIONS` binding names distinct production and preview buckets; operational
setup and credential scope are documented in
[`docs/operations/publish-to-r2.md`](docs/operations/publish-to-r2.md).

## Public publication contracts

`quantbrief.publication` owns the provider-independent publisher and version 1 JSON
contracts. Its object-storage seam requires only reads and conditional writes; the
publisher uploads and verifies a dated Public Export before it conditionally replaces
the history index, then retains the publication receipt. A failed verification cannot
advertise an Edition, and a conflicting index version rejects the stale publisher.
Public Export sanitization is allowlist-only: unknown Edition or Card fields are
dropped before hashing or upload. A public Card `id` is the lowercase 16-character
SHA-256 prefix derived by the Pipeline from the canonical source identity; it remains
stable across Editions and editorial rewrites. Edition object keys use ISO Singapore
dates, while the compatibility input may still contain the legacy dotted date.

The history index is newest-first, contains at most one entry per Edition, and names
the latest Edition explicitly. A publication receipt binds the canonical snapshot
hash, sanitized export hash, Edition/index/receipt keys, prior and resulting index
hashes, optional deployment identifier, timestamp, and outcome. Provider adapters
must transport these shapes without extending them.

`python -m quantbrief.publish_cli` is the single public publication entry point for
both GitHub Actions and the operator PowerShell command. It enforces the complete
bilingual 15-Card gate and publishes through `Publisher`. Callers retain orchestration
they uniquely own, such as source collection, Fetch State commits, or Worker deployment.

`python -m quantbrief.archive_sync_cli` verifies indexed production Public Exports
before idempotently importing them into the local Archive. Legacy Git history remains
an import-only backfill; new Edition content is not committed to Git.

Each changed public state also retains content-addressed Edition versions and index
snapshots under publication-private prefixes. `python -m quantbrief.restore_cli`
verifies those immutable objects, repairs overwritten dated objects when necessary,
and conditionally repoints only the active public index. Restore receipts belong under
the ignored local `storage/receipts/` tree or another operator-controlled evidence
store; recovery never mutates the private Archive or canonical Edition Snapshots.

## Safe change routes

- New source: add one adapter in `sources.py`, register it in `ADAPTERS`, add source
  configuration, and test source parsing plus Pipeline behavior.
- New ranking rule: change `ranking.py`; preserve the `RankedItem` result shape and
  test observable ordering and score evidence.
- New Knowledge Card field: update `models.py`, serialization, Archive ingestion if
  indexed, `web/lib/cards.ts`, UI consumers, tests, and `CONTEXT.md` when it adds a
  domain term.
- New product module: first place it in this dependency graph, then add its explicit
  allowlist entry to `scripts/check-repository.py` in the same change.
- Risky or multi-session work: create an execution plan from
  `docs/exec-plans/template.md` and keep its decisions and verification current.

Run `./scripts/verify-change.ps1` before handing off a change. The same architecture,
Python, and web checks run on pull requests.
