@echo off
setlocal
REM %~dp0 expands to the directory of this .cmd, with trailing backslash
set SCRIPT_DIR=%~dp0
"%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%proj_ttrack.py" %*
endlocal