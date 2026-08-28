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
    $singaporeTimeZone = [System.TimeZoneInfo]::FindSystemTimeZoneById('Singapore Standard Time')
    $editionDate = [System.TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow, $singaporeTimeZone)
    $editionDirectory = Join-Path $projectRoot (
        'storage/editions/{0}/{1}/{2}' -f $editionDate.ToString('yyyy'), $editionDate.ToString('MM'), $editionDate.ToString('yyyy-MM-dd')
    )
    $editionSnapshot = Join-Path $editionDirectory 'quant-brief-edition.json'

    & $python.Source -m quantbrief.cli `
        --env-file .env.local `
        --require-ai `
        --state storage/state/local-fetch-state.json `
        --output $editionSnapshot `
        --archive storage/archive/quant-brief.sqlite3
    $runExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($runExitCode -ne 0) {
    exit $runExitCode
}
