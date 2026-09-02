[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$webRoot = Join-Path $repositoryRoot 'web'
$generatedConfigPath = Join-Path $webRoot 'dist/server/wrangler.json'
$env:WRANGLER_WRITE_LOGS = 'false'
$env:WRANGLER_LOG_PATH = Join-Path $webRoot '.wrangler/logs'

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    $bundledNode = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
    if (Test-Path -LiteralPath $bundledNode) {
        $env:PATH = "$(Split-Path -Parent $bundledNode);$env:PATH"
    }
}
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    throw 'pnpm is required for preview deployment.'
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw 'Node.js 22 or newer is required for preview deployment.'
}

$env:CLOUDFLARE_ENV = 'preview'
& pnpm --dir $webRoot build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$generated = Get-Content -LiteralPath $generatedConfigPath -Raw | ConvertFrom-Json
$binding = @($generated.r2_buckets) | Where-Object { $_.binding -eq 'PUBLIC_EDITIONS' }
if ($generated.targetEnvironment -ne 'preview' -or
    $generated.name -ne 'jerome-brief-preview' -or
    @($generated.routes).Count -ne 0 -or
    $generated.workers_dev -ne $true -or
    @($binding).Count -ne 1 -or
    $binding.bucket_name -ne 'jerome-brief-preview') {
    throw 'Refusing deployment: generated Worker configuration is not isolated preview.'
}

$node = (Get-Command node -ErrorAction Stop).Source
$wrangler = Join-Path $webRoot 'node_modules/wrangler/bin/wrangler.js'
$arguments = @($wrangler, 'deploy')
if ($DryRun) { $arguments += '--dry-run' }
Push-Location $webRoot
try {
    & $node @arguments
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
