#!/bin/sh
set -e

echo "==> Running database migrations..."
python -m alembic upgrade head

# SQLite supports only 1 writer at a time; use multiple workers only with PostgreSQL.
if echo "${DATABASE_URL:-sqlite}" | grep -q 'postgresql'; then
  WORKERS=${WORKERS:-2}
else
  WORKERS=1
fi

echo "==> Starting server with ${WORKERS} worker(s)..."
exec uvicorn main:app --host 0.0.0.0 --port 8002 --workers "${WORKERS}"
