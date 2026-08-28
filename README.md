# Quant Brief

Daily quant, AI and useful-tool signals turned into traceable Chinese knowledge cards.

Quant Brief collects structured feeds and official release data, normalizes and deduplicates them, ranks the most useful items for quantitative research, and publishes a daily card feed. Every card links to an internal summary page and then back to its canonical source.

## What is included

- arXiv `q-fin`, `cs.LG`, and `cs.CL` feeds
- Hugging Face Daily Papers
- Quantocracy and selected quantitative-finance newsletters
- GitHub releases for TradingAgents, Qlib, RD-Agent, Chatbox, Claude Code, and Codex
- Source-based summaries when no model key is configured
- Optional Chinese structured summaries through OpenAI or DeepSeek
- A responsive card feed with domain filters and traceable detail pages
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

## Local long-term archive

GitHub remains the reliable daily runner and public transport for the latest edition. Your durable history lives locally in SQLite and is ignored by Git:

```powershell
./scripts/sync-local.ps1
```

The script pulls new daily commits and imports every unseen historical version of `web/data/cards.json` into `data/quant-brief.sqlite3`. It is idempotent, so missed days are recovered the next time your computer is online. A local collection can archive immediately with `python -m quantbrief.cli --archive data/quant-brief.sqlite3`.

The public website continues to read only the latest sanitized JSON snapshot. API keys, HTTP state, and the local SQLite database are never exposed to visitors.

## Optional AI summaries

Choose either provider by adding its key as a repository Actions secret:

- OpenAI: `OPENAI_API_KEY` (default model `gpt-5.6-luna`)
- DeepSeek: `DEEPSEEK_API_KEY` (default model `deepseek-v4-flash`)

`SUMMARY_PROVIDER` is an optional repository variable with values `auto`, `openai`, or `deepseek`. In `auto` mode, OpenAI is preferred when both keys exist, otherwise DeepSeek is used. You can override DeepSeek with repository variables `DEEPSEEK_MODEL` and `DEEPSEEK_BASE_URL`. When no key is present, the pipeline remains operational and labels cards as source-summary based.

Never commit access tokens or paste them into source files, workflow YAML, or remote URLs. GitHub Actions uses its short-lived built-in `GITHUB_TOKEN` for public GitHub data and committing the generated edition.

## Source configuration

Edit `config/sources.toml` to enable, disable, prioritize, or cap a source. New source types belong behind the source-adapter seam in `quantbrief/sources.py`; ranking, deduplication, summaries, and publishing remain behind the `Pipeline` interface.

## Disclaimer

Generated summaries are research navigation aids, not investment advice. Verify claims, datasets, methods, licenses, and conclusions against the linked original source.
