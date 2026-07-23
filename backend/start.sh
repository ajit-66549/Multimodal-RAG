#!/bin/sh

set -e

echo "Waiting for database migrations to succeed..."

until alembic upgrade head; do
  echo "Database is not ready yet or migration failed. Retrying in 2 seconds..."
  sleep 2
done

echo "Starting FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000