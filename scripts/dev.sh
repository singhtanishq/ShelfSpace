#!/usr/bin/env bash
# Start backend + frontend for local development.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d backend/.venv ]; then
  echo "→ Creating backend virtualenv…"
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install --quiet -r backend/requirements-dev.txt
fi

if [ ! -d frontend/node_modules ]; then
  echo "→ Installing frontend dependencies…"
  (cd frontend && npm install --no-audit --no-fund)
fi

echo "→ Applying migrations & seeding (idempotent)…"
(cd backend && .venv/bin/alembic upgrade head && .venv/bin/python -m app.db.seed)

echo "→ Starting API on :8000 and web on :5173 (Ctrl+C to stop)"
(cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000) &
(cd frontend && npm run dev) &
wait
