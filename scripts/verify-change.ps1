[CmdletBinding()]
param(
    [switch]$SkipWeb
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Initialize-WebToolchain {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        $BundledNode = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
        if (Test-Path -LiteralPath $BundledNode) {
            $env:PATH = "$(Split-Path -Parent $BundledNode);$env:PATH"
        }
    }
    if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
        $BundledPnpm = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
        if (Test-Path -LiteralPath $BundledPnpm) {
            $env:PATH = "$(Split-Path -Parent $BundledPnpm);$env:PATH"
        }
    }
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        throw "Node.js 22 or newer is required for web verification. Install Node.js or run with -SkipWeb."
    }
    if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
        throw "pnpm is required for web verification. Install pnpm or run with -SkipWeb."
    }
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Verification command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
}

Push-Location $RepositoryRoot
try {
    Invoke-Checked python scripts/check-repository.py
    Invoke-Checked python -m unittest discover -s tests -v

    if (-not $SkipWeb) {
        Initialize-WebToolchain
        Push-Location (Join-Path $RepositoryRoot "web")
        try {
            Invoke-Checked pnpm test
            Invoke-Checked pnpm lint
            Invoke-Checked pnpm build
        }
        finally {
            Pop-Location
        }
    }
}
finally {
    Pop-Location
}
