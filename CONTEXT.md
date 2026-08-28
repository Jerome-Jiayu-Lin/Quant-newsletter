# Quant Brief

Quant Brief turns newly published research and tool updates into traceable daily knowledge cards while preserving a private, durable local history.

## Language

**Edition**:
The complete selected set of Knowledge Cards for one Singapore calendar date.
_Avoid_: Daily data, newsletter dump, batch, result

**Knowledge Card**:
A classified bilingual editorial record containing localized titles and summaries, Features, provenance, and an original link.
_Avoid_: Item, row, article data, card data

**Feature**:
A stable, searchable characteristic supported by source metadata or content evidence and presented with Chinese and English labels.
_Avoid_: Free-form tag, keyword, category

**Facet**:
The controlled dimension that groups comparable Features, such as platform, topic, artifact type, or ranking.
_Avoid_: Feature type, tag group

**Editorial Tag**:
A descriptive phrase produced during summarization that aids reading but is not guaranteed to remain stable enough for filtering.
_Avoid_: Feature, filter

**Edition Snapshot**:
The immutable-shaped JSON representation of one Edition at its canonical dated local path.
_Avoid_: Output JSON, result file, cards file

**Archive**:
The local SQLite history containing Editions and their Knowledge Cards across dates.
_Avoid_: Database dump, data file, card store

**Fetch State**:
Conditional-request metadata such as ETags and last-modified values; it is operational state, not research content.
_Avoid_: Cache data, metadata file, history

**Public Export**:
A deliberately sanitized derivative of local content prepared for external website consumption.
_Avoid_: Public data, web dump, upload file
