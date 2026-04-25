#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

[ -s "$HOME/.nvm/nvm.sh" ] && . "$HOME/.nvm/nvm.sh"

if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r backend/requirements.txt
fi

if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "Created backend/.env from backend/.env.example — fill in DB credentials, then re-run." >&2
  exit 1
fi

set -a; . ./backend/.env; set +a

if [ ! -d frontend/node_modules ]; then
  ( cd frontend && npm install --silent )
fi

cleanup() { kill 0 2>/dev/null || true; }
trap cleanup EXIT INT TERM

(
  cd backend
  exec ../.venv/bin/python -m flask --app api.index run --host 0.0.0.0 --port 5000 --debug
) &

(
  cd frontend
  exec npm run dev -- --host 0.0.0.0
) &

wait
