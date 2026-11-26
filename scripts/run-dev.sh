#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ ! -f "$ROOT/backend/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/backend/.env"
  echo "Created backend/.env. Replace SECRET_KEY before deployment."
fi
(
  cd "$ROOT/backend"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python -m scripts.migrate_db
  uvicorn main:app --reload
) &
(
  cd "$ROOT/frontend"
  npm install
  npm run dev
) &
wait
