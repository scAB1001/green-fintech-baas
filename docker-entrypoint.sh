# docker-entrypoint.sh
#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; engine = create_async_engine('${DATABASE_URL}'); asyncio.run(engine.connect())" 2>/dev/null; do
  echo "Database not ready yet. Sleeping..."
  sleep 2
done

echo "Database is ready!"

# Run migrations
alembic upgrade head

# Start the application
exec uvicorn src.app.main:app --host ${UVICORN_HOST:-0.0.0.0} --port ${UVICORN_PORT:-8000} --workers ${UVICORN_WORKERS:-1}