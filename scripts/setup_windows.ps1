$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "InventoryFlow - setup" -ForegroundColor Cyan
Set-Location "$Root\backend"
py -3.12 -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

Set-Location "$Root\frontend"
npm install
npm run build
Remove-Item -Recurse -Force "$Root\backend\static" -ErrorAction SilentlyContinue
Copy-Item -Recurse ".\out" "$Root\backend\static"

Write-Host "Setup concluido." -ForegroundColor Green
Write-Host "Execute: .\scripts\run_windows.ps1"
