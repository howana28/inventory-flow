$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location "$Root\backend"
& ".\.venv\Scripts\Activate.ps1"
python -m uvicorn app.main:app --host 127.0.0.1 --port 10000 --reload
