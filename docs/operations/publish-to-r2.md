# Publish Editions to Cloudflare R2

The publication path uses two buckets so preview testing cannot mutate production:

- `jerome-brief-public` owns production Public Exports, the history index, and receipts.
- `jerome-brief-preview` owns the same key layout for preview and restore drills.

Provision them once with an authenticated Wrangler session:

```powershell
pnpm --dir web exec wrangler r2 bucket create jerome-brief-public
pnpm --dir web exec wrangler r2 bucket create jerome-brief-preview
```

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
the Worker bundle, Public Exports, or publication receipts. Install the optional
adapter dependency with `pip install -e ".[publication]"`.

The adapter talks to `https://<account-id>.r2.cloudflarestorage.com` through R2's
S3-compatible API. Creates use `If-None-Match: *`; replacements use the exact ETag
from the preceding read as `If-Match`. HTTP 409/412 conflicts are surfaced to the
publisher as stale writes and must not be bypassed with an unconditional retry.
