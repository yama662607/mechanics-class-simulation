# Thin wrapper that locates Python 3 and re-execs scripts/bootstrap.py.
# Works on Windows PowerShell 5+ and pwsh. See scripts/bootstrap.py for the
# actual logic.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$pythonCmd = $null
foreach ($candidate in @("python", "python3", "py")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $pythonCmd = $candidate
        break
    }
}

if (-not $pythonCmd) {
    Write-Error @"
Python 3 is required to run the bootstrap script.
Install Python 3.12+ from https://www.python.org/ and retry.
"@
    exit 1
}

# `py` launcher requires `-3` to pick Python 3 explicitly on systems where
# Python 2 may also be present.
$pyArgs = @()
if ($pythonCmd -eq "py") {
    $pyArgs += "-3"
}
$pyArgs += (Join-Path $ScriptDir "bootstrap.py")
$pyArgs += $args

& $pythonCmd @pyArgs
exit $LASTEXITCODE
