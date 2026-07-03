@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" scripts\run_api.py %*
) else (
    echo Skapar .venv och installerar beroenden...
    python -m venv .venv
    ".venv\Scripts\pip.exe" install -r requirements.txt
    ".venv\Scripts\python.exe" scripts\run_api.py %*
)
