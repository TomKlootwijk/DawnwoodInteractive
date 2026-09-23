# Starts the installed Codex desktop app with its bundled modern Git first in PATH.
# PATH changes apply only to this launcher and the app it starts.
[CmdletBinding()]
param([switch]$CheckOnly)

$ErrorActionPreference = 'Stop'
$previousPath = $env:Path

try {
    $gitDirectory = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd'
    $gitExecutable = Join-Path $gitDirectory 'git.exe'
    if (-not (Test-Path -LiteralPath $gitExecutable -PathType Leaf)) {
        throw "The bundled Git is missing: $gitExecutable"
    }

    $env:Path = $gitDirectory + ';' + $previousPath
    $resolvedGit = (Get-Command git.exe -CommandType Application | Select-Object -First 1).Source
    if ($resolvedGit -ne $gitExecutable) {
        throw "Windows resolved a different Git: $resolvedGit"
    }
    $gitVersion = & $gitExecutable --version
    if ($LASTEXITCODE -ne 0) { throw 'The bundled Git could not start.' }

    $repository = Split-Path -Parent $PSScriptRoot
    $statusOutput = & $gitExecutable -C $repository -c attr.tree= -c core.attributesFile= -c safe.bareRepository=explicit -c core.hooksPath=NUL -c core.fsmonitor= status --renames --porcelain=v1 -z --untracked-files=normal 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "The Git command required by Codex failed: $statusOutput"
    }

    $package = Get-AppxPackage -Name 'OpenAI.Codex' | Sort-Object { [version]$_.Version } -Descending | Select-Object -First 1
    if ($null -eq $package) { throw 'The Codex desktop package is not installed for this Windows user.' }
    $appExecutable = Join-Path $package.InstallLocation 'app\ChatGPT.exe'
    if (-not (Test-Path -LiteralPath $appExecutable -PathType Leaf)) {
        throw "The Codex executable is missing: $appExecutable"
    }

    if ($CheckOnly) {
        [pscustomobject]@{
            Git = $resolvedGit
            Version = $gitVersion
            WorktreeStatusCommand = 'Passed'
            App = $appExecutable
            AppStarted = $false
        }
        return
    }

    $runningApp = Get-Process -Name ChatGPT -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $appExecutable }
    if ($runningApp) {
        throw 'Fully quit Codex first, then open this launcher again. An already-running app retains its old Git PATH.'
    }

    Write-Host "Starting Codex with $gitVersion"
    # This is the interactive app the user is opening, so its window should be visible.
    Start-Process -FilePath $appExecutable -WorkingDirectory $repository -WindowStyle Normal
} catch {
    if ($CheckOnly) { throw }
    Write-Host $_.Exception.Message -ForegroundColor Red
    [void](Read-Host 'Press Enter to close')
    exit 1
} finally {
    $env:Path = $previousPath
}
