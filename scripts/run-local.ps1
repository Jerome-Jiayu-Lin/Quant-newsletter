param(
    [string]$EditionDate
)

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
    if ($EditionDate) {
        $parsedEditionDate = [DateTime]::MinValue
        $validDate = [DateTime]::TryParseExact(
            $EditionDate,
            'yyyy-MM-dd',
            [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::None,
            [ref]$parsedEditionDate
        )
        if (-not $validDate) {
            throw 'EditionDate must use YYYY-MM-DD.'
        }
        $editionDateValue = $parsedEditionDate
    }
    else {
        $editionDateValue = [System.TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow, $singaporeTimeZone)
    }
    $editionDateText = $editionDateValue.ToString('yyyy-MM-dd')
    $editionDirectory = Join-Path $projectRoot (
        'storage/editions/{0}/{1}/{2}' -f $editionDateValue.ToString('yyyy'), $editionDateValue.ToString('MM'), $editionDateText
    )
    $editionSnapshot = Join-Path $editionDirectory 'quant-brief-edition.json'

    & $python.Source -m quantbrief.cli `
        --edition-date $editionDateText `
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
