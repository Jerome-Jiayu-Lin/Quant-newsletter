$ErrorActionPreference = 'Stop'

$singaporeTimeZone = [System.TimeZoneInfo]::FindSystemTimeZoneById('Singapore Standard Time')
$singaporeNow = [System.TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow, $singaporeTimeZone)
$editionDate = $singaporeNow.Date.AddDays(-1).ToString('yyyy-MM-dd')

& (Join-Path $PSScriptRoot 'run-local.ps1') -EditionDate $editionDate
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& (Join-Path $PSScriptRoot 'publish-edition.ps1') -EditionDate $editionDate
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
