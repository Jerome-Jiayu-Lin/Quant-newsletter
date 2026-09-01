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
| `pipeline` | Edition orchestration and public export creation | all modules above except `archive` |
| `archive` | Durable Edition ingestion and search | none |
| `cli` | Operator entry point and dependency assembly | `pipeline`, `archive` |

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

## Runtime ownership

| State | Owner | Canonical location |
|---|---|---|
| Fetch State | `HttpClient` | `storage/state/local-fetch-state.json` |
| Candidate Pool | `CandidatePool` | `storage/candidates/rolling-candidate-pool.json` |
| Edition Snapshot | `Pipeline` | `storage/editions/YYYY/MM/YYYY-MM-DD/quant-brief-edition.json` |
| Archive | `CardArchive` | `storage/archive/quant-brief.sqlite3` |
| Public Export | publication script | `web/data/cards.json` |

All `storage/` content is ignored. Re-running an Edition updates its canonical path
idempotently.

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
