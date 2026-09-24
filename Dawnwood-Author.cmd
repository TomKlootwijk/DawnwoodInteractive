@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="run" goto resident
if /I "%~1"=="inspect" goto resident
set "DW_SOURCE_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%DW_SOURCE_PYTHON%" goto python
set "DW_SOURCE_PYTHON=python"
:python
"%DW_SOURCE_PYTHON%" -X utf8 -B local_lab\source_program.py %*
exit /b %errorlevel%
:resident
call Dawnwood-Resident2.cmd %*
exit /b %errorlevel%
