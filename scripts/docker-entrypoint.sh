#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

serious() {
    echo -e "${ORANGE}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

info() {
    echo -e "${BLUE}  $1${NC}"
}

data() {
    echo -e "${NC}  > $1${NC}"
}

echo "========================================="
success "Starting Green FinTech BaaS API Container"
echo "========================================="
info "Environment: ${ENVIRONMENT:-development}"
echo "========================================="

# Function to wait for database
wait_for_db() {
    info "Waiting for database to be ready..."
    local retries=30
    local count=0

    # Extract host and port from DATABASE_URL
    if [[ -n "$DATABASE_URL" ]]; then
        # Parse host and port from DATABASE_URL
        # Format: postgresql+asyncpg://user:pass@host:port/dbname
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

        if [[ -z "$DB_PORT" ]]; then
            DB_PORT=5432
        fi
    else
        DB_HOST="db"
        DB_PORT=5432
    fi

    while ! nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
        count=$((count + 1))
        if [ $count -ge $retries ]; then
            error "Database not ready after $retries attempts. Exiting."
            exit 1
        fi
        warn "Database not ready yet... ($count/$retries)"
        sleep 2
    done
    success "Database is ready!"
}

# Function to run migrations
run_migrations() {
    echo "Running database migrations..."
    if alembic upgrade head; then
        success "Migrations completed successfully"
    else
        error "Migrations failed"
        exit 1
    fi
}

# Function to create initial data (optional)
create_initial_data() {
    if [ "${CREATE_INITIAL_DATA:-false}" = "true" ]; then
        info "Creating initial data..."
        python -m app.scripts.init_data || true
    fi
}

# Main execution
main() {
    # Wait for database if DATABASE_URL is set
    if [[ -n "$DATABASE_URL" ]]; then
        wait_for_db
        run_migrations
        create_initial_data
    else
        warn "DATABASE_URL not set - skipping database setup"
    fi

    # Start the application
    info "Starting Uvicorn server..."
    echo "========================================="

    # Development mode
    if [ "${ENVIRONMENT:-development}" = "development" ]; then
        exec uvicorn src.app.main:app \
            --host ${HOST:-0.0.0.0} \
            --port ${PORT:-8000} \
            --reload \
            --log-level debug
    # Production mode
    else
        exec uvicorn src.app.main:app \
            --host ${HOST:-0.0.0.0} \
            --port ${PORT:-8000} \
            --workers ${WORKERS:-4} \
            --log-level info \
            --proxy-headers \
            --forwarded-allow-ips '*'
    fi
}

# Run main function
main
