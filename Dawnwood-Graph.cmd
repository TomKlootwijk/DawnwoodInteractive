@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="run" goto resident
if /I "%~1"=="inspect" goto resident
if /I "%~1"=="results" goto results
set "DW_GRAPH_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%DW_GRAPH_PYTHON%" goto python
set "DW_GRAPH_PYTHON=python"
:python
"%DW_GRAPH_PYTHON%" -X utf8 -B local_lab\source_graph_program.py %*
exit /b %errorlevel%
:resident
call Dawnwood-Resident2.cmd %*
exit /b %errorlevel%
:results
call Dawnwood-Enzyme.cmd %*
exit /b %errorlevel%
