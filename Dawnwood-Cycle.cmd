@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="run" goto resident
if /I "%~1"=="inspect" goto resident
set "DW_CYCLE_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%DW_CYCLE_PYTHON%" goto python
set "DW_CYCLE_PYTHON=python"
:python
"%DW_CYCLE_PYTHON%" -X utf8 -B local_lab\source_cycle.py %*
exit /b %errorlevel%
:resident
call Dawnwood-Resident2.cmd %*
exit /b %errorlevel%
