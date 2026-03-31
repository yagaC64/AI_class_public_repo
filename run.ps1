$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

$pythonCommand = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = @("py", "-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = @("python")
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCommand = @("python3")
} else {
    throw "Python 3 is required to run this launcher."
}

$pythonArgs = @()
if ($pythonCommand.Length -gt 1) {
    $pythonArgs += $pythonCommand[1..($pythonCommand.Length - 1)]
}
$pythonArgs += "scripts/run_menu.py"
$pythonArgs += $args

& $pythonCommand[0] @pythonArgs
exit $LASTEXITCODE
