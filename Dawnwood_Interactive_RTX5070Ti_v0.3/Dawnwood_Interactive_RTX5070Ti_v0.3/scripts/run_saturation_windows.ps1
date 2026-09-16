param([string]$Report = 'work\rtx5070ti_saturation.json')
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Push-Location $Root
try {
    $Exe = Join-Path $Root 'build\Release\dawnwood.exe'
    if (!(Test-Path $Exe)) { throw 'Build the kernel first with scripts\build_windows.ps1' }
    & $Exe --codec bc5 --fill 0.98 --reserve-mib 256 --steps 0 --report $Report
    if ($LASTEXITCODE -ne 0) { throw 'Kernel exited with an error' }
} finally { Pop-Location }
