$ErrorActionPreference = 'Stop'

git pull --ff-only
python -m quantbrief.archive --database storage/archive/quant-brief.sqlite3

$productionAccess = [Environment]::GetEnvironmentVariable('R2_PRODUCTION_ACCESS_KEY_ID', 'User')
$productionSecret = [Environment]::GetEnvironmentVariable('R2_PRODUCTION_SECRET_ACCESS_KEY', 'User')
if ([string]::IsNullOrWhiteSpace($productionAccess) -or [string]::IsNullOrWhiteSpace($productionSecret)) {
    throw 'Production R2 credentials are required to synchronize current Editions.'
}
$env:R2_ACCESS_KEY_ID = $productionAccess
$env:R2_SECRET_ACCESS_KEY = $productionSecret
$env:R2_BUCKET_NAME = 'jerome-brief-public'
python -m quantbrief.archive_sync_cli --database storage/archive/quant-brief.sqlite3
