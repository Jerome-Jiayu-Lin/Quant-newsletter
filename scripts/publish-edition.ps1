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
$websiteDataset = Join-Path $projectRoot 'web/data/cards.json'

if (-not (Test-Path -LiteralPath $editionSnapshot)) {
    throw "Edition Snapshot not found: $editionSnapshot"
}

$expectedEdition = $EditionDate.Replace('-', '.')
$deploymentIdentifier = 'operator:' + $EditionDate
& python -m quantbrief.publish_cli $editionSnapshot --compatibility-export $websiteDataset --deployment-identifier $deploymentIdentifier
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$pnpm = Get-Command pnpm -ErrorAction SilentlyContinue
if (-not $pnpm) {
    throw 'pnpm was not found in PATH.'
}
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    $dependencyRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $pnpm.Source))
    $bundledNode = Join-Path $dependencyRoot 'node/bin/node.exe'
    if (-not (Test-Path -LiteralPath $bundledNode)) {
        throw 'Node.js was not found in PATH or beside the bundled pnpm runtime.'
    }
    $nodeDirectory = Split-Path -Parent $bundledNode
    $nodeExecutable = $bundledNode
}
else {
    $nodeDirectory = Split-Path -Parent $node.Source
    $nodeExecutable = $node.Source
}

$originalPath = $env:PATH
$originalCi = $env:CI
$originalConfirmModulesPurge = $env:npm_config_confirm_modules_purge
$env:PATH = $nodeDirectory + [System.IO.Path]::PathSeparator + $env:PATH
$env:CI = 'true'
$env:npm_config_confirm_modules_purge = 'false'
Push-Location (Join-Path $projectRoot 'web')
try {
    & $pnpm.Source test
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    & $pnpm.Source build
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
    $env:PATH = $originalPath
    $env:CI = $originalCi
    $env:npm_config_confirm_modules_purge = $originalConfirmModulesPurge
}

$remoteUrl = (& git -C $projectRoot remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remoteUrl)) {
    throw 'Git origin is not configured.'
}

$originalGitSshCommand = $env:GIT_SSH_COMMAND
$repositoryKey = Join-Path $env:USERPROFILE '.ssh/quant_newsletter_codex_ed25519'
if ($remoteUrl -match '^(ssh://|git@)' -and (Test-Path -LiteralPath $repositoryKey)) {
    $gitKeyPath = $repositoryKey.Replace('\', '/')
    $env:GIT_SSH_COMMAND = "ssh -o BatchMode=yes -o IdentitiesOnly=yes -i $gitKeyPath"
}

$temporaryRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$publishCheckout = Join-Path $temporaryRoot ('quant-brief-publish-' + [guid]::NewGuid().ToString('N'))
$resolvedCheckout = [System.IO.Path]::GetFullPath($publishCheckout)
if (-not $resolvedCheckout.StartsWith($temporaryRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Temporary publish checkout escaped the OS temporary directory: $resolvedCheckout"
}
try {
    $cloneSucceeded = $false
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        & git clone --depth 1 --branch main --single-branch $remoteUrl $publishCheckout
        if ($LASTEXITCODE -eq 0) {
            $cloneSucceeded = $true
            break
        }
        if (Test-Path -LiteralPath $publishCheckout) {
            Remove-Item -LiteralPath $publishCheckout -Recurse -Force
        }
        if ($attempt -lt 3) {
            Write-Warning "Git clone attempt $attempt failed; retrying in 5 seconds."
            Start-Sleep -Seconds 5
        }
    }
    if (-not $cloneSucceeded) {
        throw 'Unable to clone origin/main after 3 attempts.'
    }

    $publishDataset = Join-Path $publishCheckout 'web/data/cards.json'
    Copy-Item -LiteralPath $editionSnapshot -Destination $publishDataset -Force

    & git -C $publishCheckout config user.name 'quant-brief-bot'
    & git -C $publishCheckout config user.email 'quant-brief-bot@users.noreply.github.com'
    & git -C $publishCheckout add -- web/data/cards.json
    & git -C $publishCheckout diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Output "website already publishes Edition $expectedEdition"
    }
    else {
        & git -C $publishCheckout commit -m "data: publish $EditionDate brief" -- web/data/cards.json
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
        & git -C $publishCheckout push origin main
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
        Write-Output "published Edition $expectedEdition to website data"
    }
}
finally {
    if (Test-Path -LiteralPath $resolvedCheckout) {
        Remove-Item -LiteralPath $resolvedCheckout -Recurse -Force
    }
    $env:GIT_SSH_COMMAND = $originalGitSshCommand
}

$wrangler = Join-Path $projectRoot 'web/node_modules/wrangler/bin/wrangler.js'
if (-not (Test-Path -LiteralPath $wrangler)) {
    throw 'Wrangler was not found in web/node_modules.'
}
Push-Location (Join-Path $projectRoot 'web')
try {
    & $nodeExecutable $wrangler deploy
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}
Write-Output "deployed Edition $expectedEdition to https://jeromebrief.com"
