# Quant Brief

Daily quant, AI and useful-tool signals turned into traceable bilingual knowledge cards.

Quant Brief collects structured feeds and official release data, normalizes and deduplicates them, ranks the most useful items for quantitative research, and publishes a daily card feed. Every card links to an internal summary page and then back to its canonical source.

## What is included

- arXiv `q-fin`, `cs.LG`, and `cs.CL` feeds
- Hugging Face Daily Papers
- Quantocracy and selected quantitative-finance newsletters
- The first three history-eligible repositories from GitHub Daily Trending
- Recent videos from QuantInsti, Hugging Face, and DeepLearning.AI
- GitHub releases for the quant-focused TradingAgents, Qlib, and RD-Agent projects
- Source-based summaries when no model key is configured
- Required DeepSeek-generated Chinese and English summaries in the scheduled Edition
- A responsive card feed with domain filters and traceable detail pages
- Stable bilingual Features for filtering by platform, artifact, topic, and method
- Independent Chinese and English editorial fields while preserving the exact original title
- A scheduled GitHub Actions workflow for the daily edition

The first implementation intentionally leaves Reddit, YouTube transcripts, paywalled newsletters, and aggressive HTML scraping disabled because their access and reuse constraints need separate review.

## Run locally

Requires Python 3.11+, Node.js 22+, and pnpm.

```bash
python -m unittest discover -s tests -v
python -m quantbrief.cli
cd web
pnpm install
pnpm dev
```

The generated edition is written to `web/data/cards.json`. The website uses that bundled file locally and reads the latest copy from the public `main` branch when hosted.

## Local API-first run

Copy `.env.local.example` to `.env.local`, add either a DeepSeek or OpenAI key, then run:

```powershell
Copy-Item .env.local.example .env.local
./scripts/run-local.ps1
```

This local-only command uses its own ignored HTTP state, fetches sources, requires successful Chinese AI summaries, writes the daily Edition Snapshot to `storage/editions/YYYY/MM/YYYY-MM-DD/quant-brief-edition.json`, and appends the Edition to `storage/archive/quant-brief.sqlite3`. If the key, model, endpoint, or returned JSON is invalid, the command stops instead of silently storing English fallback summaries. The API key remains in the ignored `.env.local` file and is never sent to the website or committed to Git.

The daily local automation updates the previous complete Singapore calendar day through a fixed operator entry point:

```powershell
./scripts/update-previous-edition.ps1
```

Website publication uses `./scripts/publish-edition.ps1 -EditionDate YYYY-MM-DD`. It validates and builds the website, then publishes only `web/data/cards.json` to `main` from a clean temporary checkout, so unrelated local changes are never included in the publication commit. For an explicit historical date, run `./scripts/run-local.ps1 -EditionDate YYYY-MM-DD`. Re-running the same date updates the canonical Edition Snapshot and Archive entry idempotently.

## Local long-term archive

GitHub remains the reliable daily runner and public transport for the latest edition. Your durable history lives locally in SQLite and is ignored by Git:

```powershell
./scripts/sync-local.ps1
```

The script pulls new daily commits and imports every unseen historical version of `web/data/cards.json` into `storage/archive/quant-brief.sqlite3`. It is idempotent, so missed days are recovered the next time your computer is online. Local runtime content is organized under `storage/archive/`, `storage/editions/`, and `storage/state/` according to `AGENTS.md`.

The public website continues to read only the latest sanitized JSON snapshot. API keys, HTTP state, and the local SQLite database are never exposed to visitors.

Each new local card contains structured `features` such as `platform:github`, `artifact:paper`, or
`topic:quantitative-finance`. A Feature has stable identity, Chinese and English labels, evidence, and confidence;
free-form model-generated `tags` remain editorial aids and are not used as durable filter keys. The Archive indexes
Features separately and supports date plus multi-Feature intersection through `CardArchive.search(...)`.

Daily ranking compares Cards inside four Content Sections: GitHub, Paper, Article, and Video. The unfiltered top three
repositories follow GitHub's verified daily order and retain stars-today plus total-star evidence; configured quant
repositories use total stars, papers prefer citations and may use platform upvotes, and YouTube feeds use views when
available. Content value rewards empirical evidence, out-of-sample validation, reproducibility, practical use, and
specific results, while link roundups are discounted. Popularity, content value, source quality, and freshness are
recorded in `scoreBreakdown`. Section minimums keep every available section represented, and the GitHub top three are
reserved before the remaining Cards compete for places. No source can contribute material older than 15 days, and
the pipeline refuses to publish an Edition when a required Content Section or one of the GitHub top three is missing.

Selection uses a 48-hour primary lane and a 15-day unpublished carryover lane. Fresh Cards compete first inside each
Content Section; carryover Cards fill only capacity that fresh Cards cannot fill. Once a Card has appeared in an
earlier Edition it is excluded from later Editions. GitHub Trending scans beyond the first three positions when a
repository has already been covered, preserving list order until three unseen repositories are found. A Trending
repository may return only when its daily star gain at least doubles to 500 or more, or its total stars grow by at
least 1,000 and 25%; a new GitHub Release has its own source URL and is naturally treated as new. The Candidate Pool
lives at `storage/candidates/rolling-candidate-pool.json`, separate from Fetch State, and GitHub Actions persists it
through the workflow cache.

## AI summaries

The scheduled GitHub Actions Edition always uses DeepSeek. Add the provided key as the
`DEEPSEEK_API_KEY` repository Actions secret; the workflow runs at 02:10 Singapore time,
updates the previous complete Singapore calendar day, and stops before publication if any
Card cannot produce complete Chinese and English editorial fields.

- DeepSeek secret: `DEEPSEEK_API_KEY` (default model `deepseek-v4-flash`)

You can override the scheduled model and endpoint with repository variables `DEEPSEEK_MODEL`
and `DEEPSEEK_BASE_URL`. A missing key, failed API request, invalid JSON response, blank
translation, or empty bilingual key-point list fails the Edition instead of publishing a
source-only fallback.

For local runs, the same DeepSeek variables live in `.env.local`. OpenAI remains available as
an explicit local alternative through `SUMMARY_PROVIDER=openai`; `OPENAI_BASE_URL` defaults to
`https://api.openai.com/v1`, and `DEEPSEEK_BASE_URL` defaults to `https://api.deepseek.com`.

Never commit access tokens or paste them into source files, workflow YAML, or remote URLs. GitHub Actions uses its short-lived built-in `GITHUB_TOKEN` for public GitHub data and committing the generated edition.

## Source configuration

Edit `config/sources.toml` to enable, disable, prioritize, or cap a source. New source types belong behind the source-adapter seam in `quantbrief/sources.py`; ranking, deduplication, summaries, and publishing remain behind the `Pipeline` interface.

## Agent-ready development

Start with [`AGENTS.md`](AGENTS.md), then use [`ARCHITECTURE.md`](ARCHITECTURE.md) as the code map and
[`docs/QUALITY.md`](docs/QUALITY.md) as the enforceable quality contract. Complex, multi-session changes use the
execution-plan lifecycle in [`docs/exec-plans/index.md`](docs/exec-plans/index.md).

Run the complete local feedback loop before handing off a change:

```powershell
./scripts/verify-change.ps1
```

The repository checker validates product-module dependency direction, declared module ownership, navigation-size
limits, required knowledge files, and root-file placement. Pull requests run the same architecture check plus Python
tests and website test, lint, and build steps.

## Disclaimer

Generated summaries are research navigation aids, not investment advice. Verify claims, datasets, methods, licenses, and conclusions against the linked original source.
