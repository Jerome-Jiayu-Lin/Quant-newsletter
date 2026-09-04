param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
    [string]$EditionDate
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$dateParts = $EditionDate.Split('-')
$editionSnapshot = Join-Path $projectRoot (
    'storage/editions/{0}/{1}/{2}/quant-brief-edition.json' -f $dateParts[0], $dateParts[1], $EditionDate
)
if (-not (Test-Path -LiteralPath $editionSnapshot)) {
    throw "Edition Snapshot not found: $editionSnapshot"
}

$productionAccess = [Environment]::GetEnvironmentVariable('R2_PRODUCTION_ACCESS_KEY_ID', 'User')
$productionSecret = [Environment]::GetEnvironmentVariable('R2_PRODUCTION_SECRET_ACCESS_KEY', 'User')
if ([string]::IsNullOrWhiteSpace($productionAccess) -or [string]::IsNullOrWhiteSpace($productionSecret)) {
    throw 'Production R2 credentials are not configured in the Windows user environment.'
}
$env:R2_ACCESS_KEY_ID = $productionAccess
$env:R2_SECRET_ACCESS_KEY = $productionSecret
$env:R2_BUCKET_NAME = 'jerome-brief-public'

$deploymentIdentifier = 'operator:' + $EditionDate
& python -m quantbrief.publish_cli $editionSnapshot --deployment-identifier $deploymentIdentifier
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$pnpm = Get-Command pnpm -ErrorAction Stop
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    $bundledNode = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
    if (-not (Test-Path -LiteralPath $bundledNode)) {
        throw 'Node.js was not found.'
    }
    $env:PATH = "$(Split-Path -Parent $bundledNode);$env:PATH"
    $node = Get-Command node -ErrorAction Stop
}

$originalCloudflareEnvironment = $env:CLOUDFLARE_ENV
$env:CLOUDFLARE_ENV = $null
$env:CI = 'true'
$env:WRANGLER_WRITE_LOGS = 'false'
$webRoot = Join-Path $projectRoot 'web'
try {
    & $pnpm.Source --dir $webRoot test
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $pnpm.Source --dir $webRoot build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $generated = Get-Content -LiteralPath (Join-Path $webRoot 'dist/server/wrangler.json') -Raw | ConvertFrom-Json
    $binding = @($generated.r2_buckets) | Where-Object { $_.binding -eq 'PUBLIC_EDITIONS' }
    if ($generated.name -ne 'jerome-brief' -or
        @($generated.routes).Count -eq 0 -or
        @($binding).Count -ne 1 -or
        $binding.bucket_name -ne 'jerome-brief-public') {
        throw 'Refusing deployment: generated Worker configuration is not production.'
    }

    $wrangler = Join-Path $webRoot 'node_modules/wrangler/bin/wrangler.js'
    Push-Location $webRoot
    try {
        & $node.Source $wrangler deploy
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:CLOUDFLARE_ENV = $originalCloudflareEnvironment
}

Write-Output "published Edition $EditionDate through production R2 and deployed https://jeromebrief.com"
