$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw 'Python 3.11 or newer was not found in PATH.'
}

Push-Location $projectRoot
$runExitCode = 0
try {
    & $python.Source -m quantbrief.cli `
        --env-file .env.local `
        --require-ai `
        --state data/local-http-state.json `
        --output data/latest.json `
        --archive data/quant-brief.sqlite3
    $runExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($runExitCode -ne 0) {
    exit $runExitCode
}
