$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..\backend')
if (-not (Test-Path '.venv')) {
    py -3.12 -m venv .venv
}
. .\.venv\Scripts\Activate.ps1
if (-not (Test-Path '.env')) {
    Copy-Item '..\.env.example' '.env'
    Write-Host 'Created backend/.env. Set SECRET_KEY before deployment.' -ForegroundColor Yellow
}
pip install -r requirements.txt
python -m scripts.migrate_db
uvicorn main:app --reload
