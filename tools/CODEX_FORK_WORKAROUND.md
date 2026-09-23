# Codex worktree fork: system Git repair

Codex's "Failed to collect untracked working tree files" error was traced to
its `git status --renames --porcelain=v1 -z --untracked-files=normal` command.
The default Git 2.17.0.windows.1 rejects `--renames` with exit code 129.
SourceTree's separate Git 2.30.2.windows.1 and the bundled Codex Git
2.53.0.windows.3 both execute the command successfully in this repository.

On 2026-09-23, the installed system Git was upgraded to 2.55.0.windows.3 using
the official Git.Git package through WinGet. The installer hash was verified
and the installation completed successfully. The ordinary PATH now resolves
`C:\Program Files\Git\cmd\git.exe` to that version, and the previously failing
status command succeeds. SourceTree settings were not changed.

The earlier custom launcher was not an established fix: after the app restarted,
the running Codex process still had the old system PATH. Its standalone command
check had passed, but that did not demonstrate that the app inherited the
changed PATH. The launcher and its desktop shortcut have been removed; use the
normal Codex launch entry.

To verify the system Git and the formerly failing command:

```powershell
git --version
git -C C:\DawnwoodInteractive -c attr.tree= -c core.attributesFile= -c safe.bareRepository=explicit -c core.hooksPath=NUL -c core.fsmonitor= status --renames --porcelain=v1 -z --untracked-files=normal
```

The status command returns exit code zero. A successful Git command alone does
not establish end-to-end success of the Codex Fork operation.
