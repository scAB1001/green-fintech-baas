# Dockerfile
# Stage 1: Builder - using uv for fast dependency installation
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Force uv to copy binaries instead of symlinking to /root/.local
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Use the python provided by the image
RUN uv venv /app/.venv --python $(which python3)

# Install dependencies into a virtual environment at /app/.venv
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application
COPY . .

# Install the application itself
RUN uv sync --frozen --no-dev

# Stage 2: Runtime - slim Python image
FROM python:3.12-slim-bookworm

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --gid 1001 app

WORKDIR /app

# Copy the venv
COPY --from=builder /app/.venv /app/.venv
COPY ./src ./src
COPY ./alembic ./alembic
COPY alembic.ini .
COPY ./scripts/docker-entrypoint.sh .

# Update permissions
USER root
RUN chown -R app:app /app && \
    chmod -R 755 /app/.venv && \
    chmod +x /app/docker-entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    VIRTUAL_ENV="/app/.venv"

USER app

# Health check (Note: localhost:8000 inside container)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/bin/bash", "./docker-entrypoint.sh"]
