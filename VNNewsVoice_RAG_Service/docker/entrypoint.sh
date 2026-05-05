#!/bin/sh
set -e

echo "[entrypoint] Running Alembic migrations..."
uv run --no-sync alembic upgrade head
echo "[entrypoint] Migrations complete. Starting server..."

exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000
