# Quant Brief Repository Rules

These rules apply to every agent and contributor working in this repository. Keep the repository navigable: every new file must have one clear owner, one clear category, and a descriptive name.

## Before creating a file

1. Search the repository for an existing module, document, script, or artifact serving the same purpose.
2. Choose the destination from the placement table below. Do not create a new top-level directory unless none of the listed categories fit.
3. Choose the final descriptive name before writing content. Names such as `data`, `output`, `result`, `new`, `temp`, `misc`, `utils`, or `test` are forbidden unless they are part of an established external convention.
4. If the file introduces a new domain term, update `CONTEXT.md` in the same change.
5. Add or update tests and documentation together with the file.

## Canonical file placement

| Content | Required location | Naming rule |
|---|---|---|
| Python product code | `quantbrief/` | `snake_case.py`; name the domain capability, such as `archive.py` or `summarize.py` |
| Python tests | `tests/` | `test_<module>.py`; mirror the product module name |
| Source configuration | `config/` | Descriptive `kebab-case` or established format name, such as `sources.toml` |
| Operator scripts | `scripts/` | Verb-first `kebab-case`, such as `run-local.ps1` or `sync-local.ps1` |
| Research notes | `docs/research/` | Descriptive topic name; include a date only when the document is time-specific |
| Architecture decisions | `docs/adr/` | `NNNN-short-decision-title.md`; create only for durable, costly-to-reverse decisions |
| Website application code | `web/app/`, `web/lib/` | Follow the framework convention and name by page or capability |
| Website static assets | `web/public/` | Descriptive purpose, such as `quant-brief-social-preview.webp` |
| Local durable database | `storage/archive/` | Exactly `quant-brief.sqlite3` unless a second archive is deliberately introduced |
| Local daily editions | `storage/editions/YYYY/MM/YYYY-MM-DD/` | Exactly `quant-brief-edition.json` inside the dated directory |
| Local fetch state | `storage/state/` | `<scope>-fetch-state.json`, such as `local-fetch-state.json` |
| GitHub workflow state | `.github/state/` | `<workflow>-fetch-state.json`, such as `daily-brief-fetch-state.json` |
| Local exports | `storage/exports/` | State the audience and content, such as `latest-public-edition.json` |
| Temporary files | Operating-system temporary directory | Never commit; remove after the operation |

The repository root is reserved for project-wide entry points and governance files such as `README.md`, `AGENTS.md`, `CONTEXT.md`, `pyproject.toml`, and `.gitignore`. Do not place generated JSON, databases, images, scratch notes, or one-off scripts at the root.

## Local edition and archive rules

- `storage/` is the only root for local runtime artifacts. Do not introduce another generic `data/`, `output/`, `results/`, or `downloads/` directory.
- A daily **Edition** is identified by its Singapore calendar date in ISO format: `YYYY-MM-DD`.
- The canonical daily snapshot path is `storage/editions/YYYY/MM/YYYY-MM-DD/quant-brief-edition.json`.
- The durable cross-day **Archive** is `storage/archive/quant-brief.sqlite3`.
- Conditional-request metadata belongs in `storage/state/local-fetch-state.json`; it is not content and must not be mixed with Editions.
- Runtime artifacts under `storage/` must remain ignored by Git. Never commit API keys, local databases, local snapshots, or fetch state.
- Re-running the same Edition must update that Edition idempotently, not create names such as `copy`, `final`, `final2`, or timestamped duplicates.
- If an export is intended for the website later, create it under `storage/exports/` with an explicit audience in the name. Do not make the website read directly from the private Archive.
- `web/data/cards.json` is a temporary website-compatibility path from the first prototype. Do not add sibling files there; migrate it during the next explicitly requested website phase.

## Knowledge Card titles and fields

- `title` is a concise Simplified Chinese editorial title, normally 12–30 Chinese characters.
- State the subject and the new finding or change. Avoid clickbait, vague titles, source names, dates, emoji, and prefixes such as “重磅”, “速看”, “最新”, or “每日精选”.
- Preserve the publisher's exact title separately as `originalTitle`; never overwrite source identity.
- `description` must explain what is new and why it may matter in one or two sentences.
- Every Card must retain `domain`, `sourceName`, `publishedAt`, `originalUrl`, `summaryProvider`, and `summaryModel` for classification and traceability.
- A Card without an original link or source identity is invalid and must not enter an Edition.

## General naming rules

- Directories: lowercase `kebab-case`, except framework-mandated names and date partitions.
- Python modules and identifiers: `snake_case`.
- PowerShell and shell scripts: verb-first `kebab-case`.
- Markdown H1 titles: describe the document's subject; never use “Notes”, “Misc”, “Untitled”, or a filename as the title.
- Dates in filenames and paths: ISO `YYYY-MM-DD`, never locale-dependent forms such as `28-08-26`.
- Use one canonical term from `CONTEXT.md`; do not alternate between “daily data”, “card file”, “digest”, and “newsletter dump”.

## Change checklist

Before finishing a change that creates or moves files, verify:

- Each file is in the category that owns it.
- Each name explains its purpose without opening the file.
- Generated and secret files are ignored by Git.
- References, scripts, tests, and documentation use the new canonical path.
- `rg` finds no stale references to the old path.
- Tests pass and `git status` contains no accidental runtime artifacts.
