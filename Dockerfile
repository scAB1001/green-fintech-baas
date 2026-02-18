# Dockerfile
# Stage 1: Builder - using uv for fast dependency installation
FROM ghcr.io/astral-sh/uv:python3.11-bookworm AS builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment at /app/.venv
# --frozen: Use lockfile without updating
# --no-dev: Exclude development dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application
COPY . .

# Install the application itself
RUN uv sync --frozen --no-dev

# Stage 2: Runtime - slim Python image
FROM python:3.11-slim-bookworm

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user for security
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --gid 1001 app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /app/.venv .venv

# Copy application code
COPY --chown=app:app ./src ./src
COPY --chown=app:app alembic.ini .
COPY --chown=app:app docker-entrypoint.sh .

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint
ENTRYPOINT ["./scripts/docker-entrypoint.sh"]
