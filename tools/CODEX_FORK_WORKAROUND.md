# Codex worktree fork on this Windows machine

Codex's "Failed to collect untracked working tree files" error was traced to
its `git status --renames --porcelain=v1 -z --untracked-files=normal` command.
The default Git 2.17.0.windows.1 rejects `--renames` with exit code 129.
SourceTree's separate Git 2.30.2.windows.1 and the bundled Codex Git
2.53.0.windows.3 both execute the command successfully in this repository.

Fully quit Codex, then launch `Start-CodexWithModernGit.ps1` using the bundled
PowerShell 7 and retry Fork. The desktop shortcut "Codex - modern Git" invokes
this script. It puts the already-installed bundled Git first in PATH only for
the app it starts. It does not change the system PATH or SourceTree settings.
Use this launcher until the default system Git is upgraded.

To check the launcher without starting or stopping Codex:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe" -NoProfile -File C:\DawnwoodInteractive\tools\Start-CodexWithModernGit.ps1 -CheckOnly
```

The check verifies Git resolution, the failing status command, and the installed
app location. A successful check is not end-to-end verification of Codex Fork;
that requires restarting the app and retrying Fork. The launcher refuses to
start while Codex is already running because a second launch would otherwise
reuse the process with the old PATH.
