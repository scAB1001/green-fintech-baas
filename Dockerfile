# Dockerfile
# --- Build Stage with uv ---
FROM ghcr.io/astral-sh/uv:python3.11-bookworm AS builder

# Install system dependencies for psycopg and other build requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Use uv to install dependencies into a virtual environment at /app/.venv
RUN uv sync --frozen --no-dev

# --- Final Runtime Stage ---
FROM python:3.11-slim-bookworm

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv .venv

# Ensure scripts in .venv/bin are executable
RUN chmod -R a+x /app/.venv/bin

# Copy application code
COPY ./src/app ./src/app
COPY alembic.ini .
COPY docker-entrypoint.sh .

# Make the entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Use slimmed-down uvicorn worker for production
ENV UVICORN_WORKERS=2
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" || exit 1

# Entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]