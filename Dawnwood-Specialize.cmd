@echo off
setlocal
cd /d "%~dp0"
set "DW_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%DW_PYTHON%" goto run
set "DW_PYTHON=python"
:run
"%DW_PYTHON%" -B local_lab\specialize.py %*
exit /b %errorlevel%
