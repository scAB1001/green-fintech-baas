#!/bin/bash
# scripts/common.sh

set -e

# --- Dynamic Path Resolution ---
# Safely resolve the project root regardless of where the script is executed from
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Setup output directory for downloads (PDFs, CSVs)
OUT_DIR="${PROJECT_ROOT}/out"
mkdir -p "$OUT_DIR"


# --- OPTIONAL ---
# Docker configurations
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

# VM configurations
# sudo sysctl vm.swappiness=1 >/dev/null 2>&1 || true
# sudo sysctl vm.overcommit_memory=1 >/dev/null 2>&1 || true

# --- Configuration & Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

COMPOSE_CMD="docker compose"

# The base URL now explicitly includes the API version routing
HOST_URL="http://localhost:8080/api/v1/"
# A secondary URL for root-level FastApi endpoints (health, docs, redoc)
ROOT_URL="http://localhost:8080"


# --- UI Helpers ---
log_warn()      { echo -e " ${YELLOW}${BOLD}⚠${YELLOW} $1${NC}"; }
log_serious()   { echo -e " ${ORANGE}${BOLD}⚠${ORANGE} $1${NC}"; }
log_error()     { echo -e " ${RED}${BOLD}✗${RED} $1${NC}"; }
log_success()   { echo -e " ${GREEN}${BOLD}✓${NC} ${GREEN}$1${NC}"; }
log_data()      { echo -e " ${NC}${BOLD}  >${NC} $1${NC}"; }
log_info()      { echo -e " ${BLUE}${BOLD}i${BLUE} $1${NC}"; }
header()        { echo -e "\n${PURPLE}${BOLD}=========== $1 ===========${NC}"; }


# Usage: assert_cmd "Success Message" "Error Message" command args...
assert_cmd() {
    local success_msg="$1"
    local error_msg="$2"
    shift 2
    # Executing the command.
    # Temporarily suppresses 'set -e' for this statement to allow graceful exit.
    if "$@"; then
        [ -n "$success_msg" ] && log_success "$success_msg"
    else
        [ -n "$error_msg" ] && log_error "$error_msg"
        exit 1
    fi
}

ask_yes_no() {
    read -p "$(echo -e "${YELLOW} ? $1 (y/N): ${NC}")" response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# --- Environment Setup ---
load_env() {
    local env_file="${PROJECT_ROOT}/.env"
    if [ -f "$env_file" ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            if [[ ! "$line" =~ ^\s*# ]] && [[ -n "$line" ]]; then
                clean_line=$(echo "$line" | sed 's/\s*#.*$//' | tr -d '\r')
                export "$clean_line"
            fi
        done < "$env_file"
    else
        log_warn "No .env file found at $env_file, using global defaults"
        export POSTGRES_USER=postgres
        export POSTGRES_PASSWORD=postgres
        export POSTGRES_DB=green_fintech
        export POSTGRES_PORT=5432
        export POSTGRES_INITDB_ARGS="--auth=scram-sha-256"
        export REDIS_PASSWORD=dev_password
        export REDIS_PORT=6379
        # export API_PORT=8080
    fi
    export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
}

# --- Generic Docker/Compose Wrappers ---
_compose_up() {
    $COMPOSE_CMD up -d "$@"
}

_compose_build_up() {
    $COMPOSE_CMD up --build -d "$@"
}

_compose_stop() {
    $COMPOSE_CMD stop "$@"
}

_compose_down() {
    $COMPOSE_CMD down "$@"
}

_compose_wipe() {
    $COMPOSE_CMD down --remove-orphans -v "$@"
}

_compose_logs() {
    local lines=${2:-20}
    $COMPOSE_CMD logs --tail="$lines" "$1"
}

_docker_ps() {
    log_info "Active Docker Containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

_docker_down_all() {
    log_warn "Tearing down the entire Docker Compose stack..."
    _compose_wipe
    log_success "Stack stopped and networks removed."
}

_docker_prune() {
    log_serious "WARNING: This removes stopped containers, unused networks, and dangling images."
    if ask_yes_no "Proceed with system prune?"; then
        docker system prune -f
        log_success "Docker environment pruned."
    fi
}
