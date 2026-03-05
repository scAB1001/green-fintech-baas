#!/bin/bash
set -e

# Use the virtual environment's executables
export PATH="/app/.venv/bin:$PATH"
export PYTHONPATH="/app/src"
VENV_PYTHON="/app/.venv/bin/python"

# Colours for logging
BLUE='\033[0;34m'
NC='\033[0m'
log_info()    { echo -e " ${BLUE}${BOLD}i${NC} ${BLUE}$1${NC}"; }

echo "========================================="
log_info "Starting Green FinTech BaaS API Container"
log_info "Environment: ${ENVIRONMENT:-development}"
echo "========================================="

# Start the application
if [ "${ENVIRONMENT:-development}" = "development" ]; then
    log_info "Starting Uvicorn in DEVELOPMENT mode (Hot-Reload Enabled)..."
    # Ensure module path matches src/app/main.py structure
    exec $VENV_PYTHON -m uvicorn src.app.main:app \
        --host ${HOST:-0.0.0.0} \
        --port ${PORT:-8000} \
        --reload \
        --log-level debug
else
    log_info "Starting Uvicorn in PRODUCTION mode (Optimized Workers)..."
    exec $VENV_PYTHON -m uvicorn src.app.main:app \
        --host ${HOST:-0.0.0.0} \
        --port ${PORT:-8000} \
        --workers ${WORKERS:-4} \
        --log-level info \
        --proxy-headers \
        --forwarded-allow-ips '*'
fi
