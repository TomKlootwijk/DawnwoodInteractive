@echo off
setlocal
cd /d "%~dp0"
set "DW_SOURCE_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%DW_SOURCE_PYTHON%" goto run
set "DW_SOURCE_PYTHON=python"
:run
"%DW_SOURCE_PYTHON%" -X utf8 -B source_workbench\Dawnwood_Interactive_v0.2\run.py %*
exit /b %errorlevel%
