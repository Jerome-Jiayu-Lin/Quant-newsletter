# Publish Editions to Cloudflare R2

The publication path uses two buckets so preview testing cannot mutate production:

- `jerome-brief-public` owns production Public Exports, the history index, and receipts.
- `jerome-brief-preview` owns the same key layout for preview and restore drills.

Both buckets were provisioned in Cloudflare account
`b07afe1e3cb22e411cabd069c6dfdf50` on 2026-09-02. Do not recreate or rename them;
the Wrangler binding and publication defaults depend on these exact names.

Provision them once with an authenticated Wrangler session:

```powershell
pnpm --dir web exec wrangler r2 bucket create jerome-brief-public
pnpm --dir web exec wrangler r2 bucket create jerome-brief-preview
```

Before provisioning, enable R2 for the target Cloudflare account in the Dashboard and
accept any account-level terms or billing confirmation shown there. `wrangler whoami`
can succeed while R2 remains disabled; `wrangler r2 bucket list` returns Cloudflare
error `10042` in that state. Enabling the product is an account-owner action and must
not be inferred from ordinary Worker deployment authorization.

The Worker reads through the `PUBLIC_EDITIONS` binding. Local `wrangler dev` uses
local persisted R2 state; remote preview uses `jerome-brief-preview` because
`preview_bucket_name` is set explicitly. Never point preview at the production bucket.

## Publisher credentials

Create a bucket-scoped R2 API token with **Object Read & Write** access to only the
target bucket. Do not grant account-wide administration, bucket creation/deletion, or
access to both preview and production from one token. The publisher reads these
server-side environment variables:

```text
CLOUDFLARE_ACCOUNT_ID
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
R2_BUCKET_NAME
```

Use `R2_BUCKET_NAME=jerome-brief-preview` for drills. Store credentials in the local
environment or CI secret store; never add them to `.env.local`, Wrangler `vars`, Git,
the Worker bundle, Public Exports, or publication receipts. Install the adapter
dependency with `python -m pip install "boto3>=1.43.84,<2"`.

Both scheduled and operator publication use the same command after an Edition
Snapshot exists:

```powershell
python -m quantbrief.publish_cli storage/editions/2026/09/2026-09-01/quant-brief-edition.json --compatibility-export web/data/cards.json --deployment-identifier operator:2026-09-01
```

The command publishes and verifies R2 first, then updates the compatibility export.
If R2 publication fails, the tracked compatibility file is left unchanged. The daily
workflow supplies the same four R2 settings through GitHub secrets and variables.

The adapter talks to `https://<account-id>.r2.cloudflarestorage.com` through R2's
S3-compatible API. Creates use `If-None-Match: *`; replacements use the exact ETag
from the preceding read as `If-Match`. HTTP 409/412 conflicts are surfaced to the
publisher as stale writes and must not be bypassed with an unconditional retry.

## Restore a verified index

Every successful publication retains immutable Edition content and an index snapshot
addressed by its SHA-256 hash. Restore by copying the target `resultingIndexHash` from
a trusted publication receipt and writing the restore receipt under the ignored local
`storage/` tree:

```powershell
python -m quantbrief.restore_cli <resulting-index-hash> --deployment-identifier preview-restore-drill --receipt storage/receipts/preview-restore-receipt.json
```

The command verifies the target index snapshot and every referenced Edition. If a
fixed dated object was overwritten, it restores that object from its verified private
content version before conditionally replacing the active index. It never modifies an
Edition Snapshot or the local Archive. A missing version, hash mismatch, or concurrent
write aborts the restore instead of forcing the index update.
