#!/bin/bash

# --- Configuration & Colors ---
set -e

# Colour Palette
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

COMPOSE_CMD="docker compose"

full_path=$(realpath $0)
dir_path=$(dirname $full_path)
out_dir="$dir_path/out"
mkdir -p "$out_dir"

# --- UI & Interaction Helpers ---
log_success() { echo -e " ${GREEN}${BOLD}✓${NC} ${GREEN}$1${NC}"; }
log_error()   { echo -e " ${RED}${BOLD}✗${NC} ${RED}$1${NC}"; }
log_info()    { echo -e " ${BLUE}${BOLD}i${NC} ${BLUE}$1${NC}"; }
log_warn()    { echo -e " ${YELLOW}${BOLD}⚠${NC} ${YELLOW}$1${NC}"; }
header()      { echo -e "\n${PURPLE}${BOLD}=========== $1 ===========${NC}"; }
opt()         { echo -ne "${NC}${BOLD}[${BLUE}$1${NC}${BOLD}]${NC}"; }

# Standardised Yes/No Prompt (DRY)
ask_yes_no() {
    read -p "$(echo -e "${YELLOW} ? $1 (y/N): ${NC}")" response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# --- Environment Setup ---
load_env() {
    # Docker configurations
    export COMPOSE_DOCKER_CLI_BUILD=1
    export DOCKER_BUILDKIT=1

    # VM configurations
    sudo sysctl vm.swappiness=1 >/dev/null 2>&1 || true
    sudo sysctl vm.overcommit_memory=1 >/dev/null 2>&1 || true

    if [ -f .env ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            if [[ ! "$line" =~ ^\s*# ]] && [[ -n "$line" ]]; then
                clean_line=$(echo "$line" | sed 's/\s*#.*$//' | tr -d '\r')
                export "$clean_line"
            fi
        done < .env
    fi
}

# --- Core command wrappers ---
_redis() {
    docker exec -e REDISCLI_AUTH="${REDIS_PASSWORD}" green-fintech-cache redis-cli "$@"
}

_redis_it() {
    docker exec -e REDISCLI_AUTH="${REDIS_PASSWORD}" -it green-fintech-cache redis-cli "$@"
}

_compose_up() {
    $COMPOSE_CMD up -d "$@"
}

_compose_build_up() {
    $COMPOSE_CMD up --build -d "$@"
}

_compose_down() {
    $COMPOSE_CMD down "$@"
}

_compose_logs() {
    local lines=${2:-20}
    $COMPOSE_CMD logs --tail="$lines" "$1"
}

# --- API HELPER FUNCTIONS ---
API_BASE_URL="http://localhost:8080"

# TODO: Use in base
# ENDPOINT_ROUTER="api/v1/"

# Usage: _api_get "/endpoint"
_api_get() {
    curl -X 'GET' "${API_BASE_URL}$1" \
        -H 'accept: application/json'
}

# Usage: _api_post "/endpoint" '{"json": "data"}'
_api_post() {
    curl -X 'POST' "${API_BASE_URL}$1" \
        -H 'Content-Type: application/json' \
        -H 'accept: application/json' \
        -d "$2"
}

# Usage: _api_delete "/endpoint"
_api_delete() {
    curl -s -X 'DELETE' "${API_BASE_URL}$1" -H 'accept: application/json'
}

# Usage: _api_status "GET" "/endpoint"
_api_status() {
    curl -s -o /dev/null \
        -w "%{http_code}" \
        -X "$1" "${API_BASE_URL}$2" \
        -H 'accept: application/json'
}

# Usage: _api_download "/endpoint" "filename.ext"
_api_download() {
    local status
    local curl_exit

    # -w "%{http_code}" captures ONLY the status code to standard out.
    status=$(curl -s -w "%{http_code}" -X 'GET' "${API_BASE_URL}$1" -o "$out_dir/$2")
    curl_exit=$? # Capture the actual exit code of the curl command itself

    # Ensure the HTTP request was OK AND curl successfully wrote the file to disk
    if [[ "$status" == "200" && "$curl_exit" -eq 0 ]]; then
        return 0
    else
        rm -f "$out_dir/$2"
        return 1
    fi
}

# --- Interactive Menu ---
show_menu() {
    clear

    local uv_cache_info="N/A"
    if command -v uv >/dev/null 2>&1; then
        uv_cache_info=$(uv cache size --preview-features cache-size 2>/dev/null || echo "Unknown")
    fi

    echo -e "${CYAN}${BOLD}🍃 Green FinTech BaaS - Interactive CLI${NC}      ${YELLOW}UV Cache:${NC} $uv_cache_info"
    echo -e "-------------------------------------------------------------------------------------"

    echo -e "${BOLD}🛠️  Core Setup & Maintenance${NC}"
    echo -e "  01) $(opt "init")        Full Install (UV)        02) $(opt "lint")        Ruff/Black/Mypy"
    echo -e "  03) $(opt "clean")       Deep Workspace Purge     04) $(opt "kill")        Kill Ports 8000 & 8080"

    echo -e "\n${BOLD}🐘 Postgres Database (Local/Docker)${NC}"
    echo -e "  05) $(opt "db-up")       Start PG Container       06) $(opt "db-seed")     Seed PG Database"
    echo -e "  07) $(opt "db-stat")     Health & Stats           08) $(opt "db-wipe")     Nuke PG Volume & Reset"

    echo -e "\n${BOLD}🚀 Redis Cache Service${NC}"
    echo -e "  09) $(opt "rd-up")       Start Redis Container    10) $(opt "rd-stat")     Ping & Key Check"

    echo -e "\n${BOLD}⚗️  Alembic Migrations${NC}"
    echo -e "  11) $(opt "mig-new")     Create Autogen Rev       12) $(opt "mig-up")      Preview & Apply"
    echo -e "  13) $(opt "mig-stat")    History & Rollback"

    echo -e "\n${BOLD}🌐 FastAPI Service${NC}"
    echo -e "  14) $(opt "api-up")      Start FastAPI Container  15) $(opt "api-stat")    Health/Docs/Endpoint"
    echo -e "  16) $(opt "run")         Local Uvicorn Server"

    echo -e "\n${BOLD}🌐 Testing, Building and Publishing${NC}"
    echo -e "  17) $(opt "test")        Pytest (Standard)        18) $(opt "e2e")         E2E (End-to-End) Test"
    echo -e "  19) $(opt "stack")       Full Docker Stack        20) $(opt "package")     Publish to [Test]PyPI"

    echo -ne "\n   q) ${NC}[${RED}Quit${NC}]        ${YELLOW}Select an option: ${NC}"

    read -r opt
    opt=$(echo "$opt" | tr '[:upper:]' '[:lower:]')

    case $opt in
        1|init)      run_script "init" ;;
        2|lint)      run_script "lint" ;;
        3|clean)     run_script "clean" ;;
        4|kill)      run_script "kill-ports" ;;
        5|db-up)     run_script "db-up" ;;
        6|db-seed)   run_script "db-seed" ;;
        7|db-stat)   run_script "db-stat" ;;
        8|db-wipe)   run_script "db-wipe" ;;
        9|rd-up)     run_script "rd-up" ;;
        10|rd-stat)  run_script "rd-stat" ;;
        11|mig-new)  run_script "mig-new" ;;
        12|mig-up)   run_script "mig-up" ;;
        13|mig-stat) run_script "mig-stat" ;;
        14|api-up)   run_script "api-up" ;;
        15|api-stat) run_script "api-stat" ;;
        16|run)      run_script "run" ;;
        17|test)     run_script "test" ;;
        18|e2e)      run_script "e2e" ;;
        19|stack)    run_script "docker-stack" ;;
        20|package)  run_script "package" ;;
        q|quit|exit) log_success "Exiting..."; exit 0 ;;
        *)  log_error "Invalid option"; sleep 1; show_menu ;;
    esac
}

# --- Command Logic ---
exec_cmd() {
    case "$1" in
        "init")
            header "INITIALISING PROJECT"
            log_info "Syncing UV environment and installing all groups..."
            uv sync --all-groups && log_success "UV environment synchronised"

            log_info "Installing pre-commit hooks..."
            uv run pre-commit install && log_success "Git hooks active"

            log_info "Updating pre-commit hooks..."
            uv run pre-commit autoupdate && log_success "Pre-commit hooks updated"

            exec_cmd "lock"
            log_success "Packages installed successfully."
            ;;

        "lock")
            header "LOCKFILE SYNCHRONISATION"
            log_info "Updating UV lock..."
            uv lock --upgrade && log_success "uv.lock upgraded to LTS"

            log_info "Checking lockfile integrity..."
            uv lock --check

            if ask_yes_no "Would you like to view the dependency tree?"; then
                uv tree --all-groups
            fi

            log_info "Exporting dependencies to requirements.txt..."
            uv export --format requirements.txt --output-file requirements.txt >/dev/null
            log_success "Lockfiles updated successfully."
            ;;

        "lint")
            header "LINTING & FORMATTING"
            log_info "Updating pre-commit hooks..."
            uv run pre-commit autoupdate && log_success "Pre-commit hooks updated"

            log_info "Running Ruff..."
            uv run ruff check --fix . && log_success "Ruff finished"

            log_info "Running Black..."
            uv run black . && log_success "Black finished"

            log_info "Running Mypy..."
            uv run mypy . && log_success "Mypy checks passed"

            log_info "Running Pre-commit hooks..."
            uv run pre-commit run --all-files
            log_success "Linting complete."
            ;;

        "clean")
            header "WORKSPACE PURGE"
            log_warn "You are about to delete all cached files, build artifacts, and docker images."
            if ask_yes_no "Proceed?"; then
                log_info "Cleaning Python caches..."
                find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
                find . -type f -name "*.py[co]" -delete 2>/dev/null || true
                log_success "Pycache removed"

                log_info "Cleaning tool artifacts..."
                rm -rf .pytest_cache .coverage .mypy_cache .ruff_cache dist build *.egg-info 2>/dev/null || true
                log_success "Tool caches and environments purged"

                log_info "Pruning UV Cache..."
                if command -v uv >/dev/null 2>&1; then
                    uv cache prune --force >/dev/null 2>&1 && log_success "UV cache pruned" || log_error "Failed to prune UV cache"
                else
                    log_warn "UV not found, skipping cache prune..."
                fi

                log_info "Pruning Docker system..."
                docker builder prune -f >/dev/null 2>&1 && log_success "Docker artifacts cleaned"

                log_info "Flushing Redis Cache..."
                if docker ps --format '{{.Names}}' | grep -q "^green-fintech-cache$"; then
                    _redis FLUSHALL >/dev/null 2>&1 && log_success "Redis cache cleared"
                fi
                log_success "Workspace cleaned."
            fi
            ;;

        "kill"|"kill-ports")
            header "PORT KILLER"
            for port in 8000 8080; do
                log_info "Checking Port $port..."
                if lsof -i :$port -t >/dev/null ; then
                    log_warn "Port $port is already in use."
                    log_info "Killing process using port $port..."
                    sudo lsof -i :$port -t | xargs sudo kill -9 2>/dev/null || true
                    log_success "Port $port is free"
                else
                    log_success "Port $port is free"
                fi
            done
            ;;
        "db-up")
            header "POSTGRES SERVICE CREATION"
            log_info "Spinning up Postgres container..."
            _compose_build_up postgres && log_success "Container started"

            log_info "Starting postgres database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            exec_cmd "db-seed" || { log_error "Seeding failed"; exit 1; }
            log_success "Postgres service is running successfully."
            ;;

        "seed"|"db-seed")
            header "POSTGRES DB INITIALISATION"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            exec_cmd "mig-new"
            exec_cmd "mig-up"
            log_success "Schema up to date"

            log_warn "Waiting for PostgreSQL to commit DDL changes..."
            sleep 2

            log_info "Seeding data..."
            uv run python -m scripts.seed_db && log_success "Seeds planted" || log_error "Seeding failed"
            log_success "Postgres db fully initialised."
            ;;

        "db-stat")
            header "DATABASE INSPECTION"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            ./scripts/db-helper.sh inspect

            log_info "Checking container logs..."
            _compose_logs postgres
            log_success "Postgres status check complete."
            ;;

        "db-wipe")
            header "DATABASE PURGE"
            log_warn "This will delete all persistent data in Postgres!"
            if ask_yes_no "Are you sure?"; then
                log_info "Stopping containers and removing volumes..."
                _compose_down -v && log_success "Environment wiped"

                if ask_yes_no "Would you like to purge Alembic history?"; then
                    rm -rf alembic/versions/*.py
                fi

                if ask_yes_no "Would you like to run 'db-up'?"; then
                    exec_cmd "db-up"
                fi
            fi
            ;;

        "db-sql")
            header "RUNNING CUSTOM SQL"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."
            ./scripts/db-helper.sh sql
            ;;

        "db-psql")
            header "POSTGRES INTERACTIVE SHELL"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."
            ./scripts/db-helper.sh psql
            ;;

        "rd-up")
            header "REDIS SERVICE CREATION"
            log_info "Spinning up Redis container..."
            _compose_build_up redis && log_success "Redis container running"

            log_info "Pinging Redis..."
            _redis ping | grep -q "PONG" && log_success "Redis is alive" || log_error "Redis unreachable"
            log_success "Redis service is running successfully."
            ;;

        "rd-stat")
            header "REDIS STATUS"
            log_info "Pinging Redis..."
            _redis ping | grep "PONG" && log_success "Redis is alive" || log_error "Redis unreachable"

            log_info "Number of existing keys..."
            _redis DBSIZE

            log_info "Performing endpoint cache test..."
            _api_get "/api/v1/companies/1"
            echo

            log_info "Checking for new keys..."
            _redis KEYS "*" | grep ":" && log_success "Data present" || log_warn "Cache empty"

            log_info "Checking container logs..."
            _compose_logs redis
            log_success "Redis status check complete."

            header "CACHING & INVALIDATION DIAGNOSTICS"
            log_info "1. Timing CSV Export (Cache Miss - DB Generation)..."
            time curl -s -o /dev/null -X 'GET' "${API_BASE_URL}/api/v1/companies/export/csv"

            echo
            log_info "2. Timing CSV Export (Cache Hit - Should be INSTANT)..."
            time curl -s -o /dev/null -X 'GET' "${API_BASE_URL}/api/v1/companies/export/csv"

            echo
            log_info "3. Timing PDF Generation (Cache Miss - CPU Generation)..."
            time curl -s -o /dev/null -X 'GET' "${API_BASE_URL}/api/v1/companies/1/simulate-loan/1/pdf"

            echo
            log_info "4. Timing PDF Generation (Cache Hit - Base64 Decode)..."
            time curl -s -o /dev/null -X 'GET' "${API_BASE_URL}/api/v1/companies/1/simulate-loan/1/pdf"

            echo
            log_info "5. Current Redis Keys (Should contain CSV and PDF):"
            _redis KEYS "*"

            log_info "6. Ingesting Barclays (01026167) to trigger POST invalidation..."
            _api_post "/api/v1/companies/" '{"company_number": "01026167"}' > /dev/null
            echo
            log_success "Ingestion complete."

            log_info "7. Checking Redis Keys (The 'companies:csv' key should be purged):"
            _redis KEYS "*"

            log_info "8. Re-caching the CSV file..."
            curl -s -o /dev/null -X 'GET' "${API_BASE_URL}/api/v1/companies/export/csv"

            log_info "9. Triggering DELETE invalidation (Removing Company ID 2)..."
            _api_delete "/api/v1/companies/2" > /dev/null
            log_success "Deletion complete."

            log_info "10. Final Redis Keys (The 'companies:csv' key should be purged again):"
            _redis KEYS "*"
            log_success "Cache behavior diagnostics complete."
            ;;

        "rd-cli")
            header "REDIS INTERACTIVE SHELL"
            log_info "Connecting to green-fintech-cache..."
            _redis_it
            ;;

        "mig-new")
            header "NEW MIGRATION"
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            log_info "Generating migration script..."
            read -p "Enter migration message: " msg
            if [ -n "$msg" ]; then
                uv run alembic revision --autogenerate -m "$msg" && log_success "Migration created in ./alembic/versions"
            else
                log_error "Migration message cannot be empty."
            fi
            ;;

        "mig-up")
            header "UPGRADING SCHEMA"
            log_info "Readying to apply..."
            if ask_yes_no "Apply migration to database?"; then
                read -p "Enter migration tag (optional): " tag
                if [ -n "$tag" ]; then
                    uv run alembic upgrade head --tag "$tag" || { log_error "Migrations failed"; exit 1; }
                else
                    uv run alembic upgrade head || { log_error "Migrations failed"; exit 1; }
                fi
                log_success "Migration applied successfully."
            else
                log_warn "Migration not applied. Remember to apply it before running the app!"
            fi
            ;;

        "mig-stat")
            header "MIGRATION STATUS"
            log_info "Checking migration history..."
            uv run alembic history --verbose | head -n 15

            log_info "Rolling back to specified revision..."
            read -p "How many revisions to rollback? (Enter number or 'n' to skip): " rev
            if [[ "$rev" =~ ^[0-9]+$ ]]; then
                log_warn "Rolling back -$rev revision(s)..."
                uv run alembic downgrade "-$rev" && log_success "Rollback complete"
            else
                log_info "Skipping rollback..."
            fi
            log_success "Migration status check complete."
            ;;

        "api-up")
            if ask_yes_no "Would you like to run 'kill-ports'?"; then exec_cmd "kill-ports"; fi

            header "FASTAPI SERVICE CREATION"
            log_info "Spinning up FastAPI container..."
            _compose_build_up api && log_success "Container started"

            log_info "Waiting for API readiness..."
            sleep 5

            [[ "$(_api_status GET /health)" == "200" ]] && log_success "API Health OK" || log_error "Health check failed"
            log_success "FastAPI service is running successfully."
            ;;

        "api-stat")
            header "FASTAPI STATUS"
            log_info "Checking Health Endpoint..."
            [[ "$(_api_status GET /health)" == "200" ]] && log_success "Health OK" || log_error "Health Failed"

            log_info "Checking OpenAPI Docs..."
            [[ "$(_api_status GET /docs)" == "200" ]] && log_success "Docs OK" || log_error "Docs unreachable"

            log_info "Ingesting TESCO PLC (00445790)..."
            _api_post "/api/v1/companies/" '{"company_number": "00445790"}' || log_error "Tesco ingestion failed"
            echo

            log_info "Ingesting SHELL PLC (04366849)..."
            _api_post "/api/v1/companies/" '{"company_number": "04366849"}' || log_error "Shell ingestion failed"
            echo

            log_info "Simulating Green Loan (Tesco)..."
            _api_post "/api/v1/companies/1/simulate-loan" '{"loan_amount": 1000000, "term_months": 120}' || log_error "Simulation failed"
            echo

            log_info "Testing CSV Bulk Export..."
            if _api_download "/api/v1/companies/export/csv" "companies_export.csv"; then
                log_success "CSV Exported successfully to companies_export.csv"
            else
                log_error "CSV Export failed"
            fi

            log_info "Testing PDF Quote Generation..."
            if _api_download "/api/v1/companies/1/simulate-loan/1/pdf" "green_loan_quote.pdf"; then
                log_success "PDF Rendered successfully to green_loan_quote.pdf"
            else
                log_error "PDF Generation failed"
            fi

            log_info "Checking container logs..."
            _compose_logs api
            log_success "FastAPI status check complete."
            ;;

        "run")
            if ask_yes_no "Would you like to run 'kill-ports'?"; then exec_cmd "kill-ports"; fi

            header "LOCAL FASTAPI SERVER"
            log_info "Starting Uvicorn..."
            uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
            ;;

        "test")
            if ask_yes_no "Would you like to run 'kill-ports'?"; then exec_cmd "kill-ports"; fi
            log_info "Wiping containers and volumes..."
            _compose_down --remove-orphans -v && log_success "Environment wiped"

            header "RUNNING TEST SUITE"
            if ask_yes_no "Run with coverage report?"; then
                log_info "Running tests with coverage report..."
                uv run pytest --cov=src --cov-report=html
                log_success "Coverage report generated in htmlcov/index.html"

                log_info "Opening coverage report in browser..."
                xdg-open htmlcov/index.html
            else
                log_info "Running tests (standard mode)..."
                uv run pytest -v && log_success "Tests passed" || log_error "Tests failed"
            fi

            if ask_yes_no "View specific tests in debug mode?"; then
                read -p "Specify the marker(s): " markers
                uv run pytest -m "$markers" -v --log-cli-level=DEBUG
            fi

            if ask_yes_no "Run specific test file or directory?"; then
                read -p "Enter test file or directory within tests/ (e.g., db_test.py): " test_path
                uv run pytest -v "$test_path"
            fi
            ;;

        "e2e")
            header "END-TO-END ARCHITECTURE TEST"
            log_info "1. Testing Database Health..."
            exec_cmd "db-stat"

            log_info "2. Testing Redis Cache..."
            exec_cmd "rd-stat"

            log_info "3. Testing FastAPI & File Generation..."
            exec_cmd "api-stat"

            header "TEST SUITE COMPLETE"
            ;;

         "stack"|"docker-stack")
            if ask_yes_no "Would you like to run 'kill-ports'?"; then exec_cmd "kill-ports"; fi
            if ask_yes_no "Would you like to run 'lock'?"; then exec_cmd "lock"; fi

            header "DOCKER COMPOSE STACK"
            log_info "Clearing space..."
            _compose_down --remove-orphans -v && log_success "Environment wiped"

            if ask_yes_no "Would you like to clear Docker artifacts?"; then
                docker builder prune -f >/dev/null 2>&1 && log_success "Docker artifacts cleaned"
            fi

            log_info "Building and starting all services..."
            if ask_yes_no "Would you like to build the containers from scratch?"; then
                _compose_build_up || { log_error "Stack failed to start."; exit 1; }
                exec_cmd "db-seed" || { log_error "Database failed to initialize."; exit 1; }
            else
                _compose_up || { log_error "Stack failed to start."; exit 1; }
                if ask_yes_no "Would you like to reinitialise the database?"; then
                    exec_cmd "db-seed" || { log_error "Database failed to initialize."; exit 1; }
                fi
            fi
            log_success "Stack running in background"

            log_info "Service Status"
            $COMPOSE_CMD ps

            sleep 2 && exec_cmd "db-stat"
            sleep 2 && exec_cmd "mig-stat"
            sleep 2 && exec_cmd "api-stat"
            sleep 2 && exec_cmd "rd-stat"

            log_success "Docker stack status check complete."
            ;;

        "down"|"docker-down")
            header "DOCKER COMPOSE DOWN"
            log_info "Viewing existing processes..."
            $COMPOSE_CMD ps

            log_info "Stopping Containers..."
            _compose_down && log_success "Environment stopped"
            ;;

        "build")
            header "PACKAGING FOR PYPI"
            log_info "Cleaning old build artifacts..."
            rm -rf dist/ build/ *.egg-info

            log_info "Building wheel and sdist with UV..."
            uv build && log_success "Build artifacts created in dist/"
            ;;

        "pack"|"package")
            exec_cmd "build"

            header "PUBLISHING TO TEST PYPI"
            log_info "Uploading package using Twine via UV..."
            uv run twine upload --repository testpypi dist/* --verbose
            ;;

        *)
            log_error "Command '$1' not found."
            ;;
    esac
}

# --- Interactive Wrapper ---
run_script() {
    local cmd=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    shift
    exec_cmd "$cmd" "$@"

    echo -e "\n${YELLOW}Press enter to return to menu...${NC}"
    read -r
    show_menu
}

# --- Execution Entry ---
load_env
if [ -z "$1" ]; then
    show_menu
else
    cmd=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    shift
    exec_cmd "$cmd" "$@"
fi
