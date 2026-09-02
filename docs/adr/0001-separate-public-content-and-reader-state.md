---
status: accepted
---

# Separate public content delivery from reader state

Quant Brief will keep its complete Archive private and local, publish dated sanitized
Public Exports to Cloudflare R2, and use Cloudflare D1 only for mutable public metadata
and reader state. Public reader identity will be provided by Clerk, while Cloudflare
Access will independently protect administrative surfaces; Workers or Pages Functions
will enforce authorization and mediate all D1 writes. This separation preserves the
existing Edition and Public Export boundary, keeps anonymous historical reading cheap
and cacheable, and avoids turning either the public database or the identity provider
into the authoritative editorial Archive.

## Considered options

- A single hosted relational database for Editions, accounts, favorites, and
  administration was rejected because historical Edition documents are append-mostly
  publication artifacts and do not require a database query for ordinary browsing.
- Publishing the local SQLite Archive directly was rejected because it mixes private
  provenance and runtime history with the deliberately sanitized public contract.
- Implementing passwords and sessions directly in D1 was rejected because credential
  recovery, abuse prevention, token security, and identity lifecycle are not Quant
  Brief domain capabilities.

## Consequences

- R2 objects and their history index must be reproducible from the local Archive and
  canonical Edition Snapshots.
- D1 may reference a published Card or Edition by stable identifier but must not be the
  only copy of editorial history.
- Reader identity identifiers, favorites, and administrative audit data must not be
  embedded in Public Exports.
- Clerk and Cloudflare integrations remain replaceable edge adapters; the Pipeline,
  Knowledge Card model, and Archive stay provider-independent.
- The services are introduced only when their corresponding product capability is
  implemented; accepting this target does not require provisioning them immediately.
