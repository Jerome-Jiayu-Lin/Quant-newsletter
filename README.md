# Quant Brief

Daily quant, AI and useful-tool signals turned into traceable bilingual knowledge cards.

Quant Brief collects structured feeds and official release data, normalizes and deduplicates them, ranks the most useful items for quantitative research, and publishes a daily card feed. Every card links to an internal summary page and then back to its canonical source.

## What is included

- arXiv `q-fin`, `cs.LG`, and `cs.CL` feeds
- Hugging Face Daily Papers
- Quantocracy and selected quantitative-finance newsletters
- GitHub Daily Trending repositories relevant to quant, AI, Skills, research, productivity, and useful tools
- GitHub releases for the quant-focused TradingAgents, Qlib, and RD-Agent projects
- Source-based summaries when no model key is configured
- Optional Chinese structured summaries through OpenAI or DeepSeek
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

Daily ranking is cohort-based rather than a single cross-format formula. Trending repositories first follow GitHub's
verified daily rank and retain stars-today plus total-star evidence; configured quant repositories use total stars,
papers prefer citations and may use platform upvotes when citations are unavailable, and future video adapters use
views. Raw popularity and age-adjusted velocity are converted to percentiles inside each content type, then combined
with research relevance and freshness. Every card stores `scoreBreakdown`; missing metrics use an explicit relevance
fallback instead of being treated as zero. Content caps in `config/sources.toml` prevent one format from occupying the
whole Edition and relax only when needed to fill the daily limit.

## Optional AI summaries

Choose either provider by adding its key as a repository Actions secret:

- OpenAI: `OPENAI_API_KEY` (default model `gpt-5.6-luna`)
- DeepSeek: `DEEPSEEK_API_KEY` (default model `deepseek-v4-flash`)

`SUMMARY_PROVIDER` is an optional repository variable with values `auto`, `openai`, or `deepseek`. In `auto` mode, OpenAI is preferred when both keys exist, otherwise DeepSeek is used. You can override DeepSeek with repository variables `DEEPSEEK_MODEL` and `DEEPSEEK_BASE_URL`. When no key is present, the pipeline remains operational and labels cards as source-summary based.

For local runs, the same variables live in `.env.local`. `OPENAI_BASE_URL` defaults to `https://api.openai.com/v1`; `DEEPSEEK_BASE_URL` defaults to `https://api.deepseek.com`.

Never commit access tokens or paste them into source files, workflow YAML, or remote URLs. GitHub Actions uses its short-lived built-in `GITHUB_TOKEN` for public GitHub data and committing the generated edition.

## Source configuration

Edit `config/sources.toml` to enable, disable, prioritize, or cap a source. New source types belong behind the source-adapter seam in `quantbrief/sources.py`; ranking, deduplication, summaries, and publishing remain behind the `Pipeline` interface.

## Disclaimer

Generated summaries are research navigation aids, not investment advice. Verify claims, datasets, methods, licenses, and conclusions against the linked original source.
