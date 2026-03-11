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

# Usage: assert_cmd "Success Message" "Error Message" command args...
assert_cmd() {
    local success_msg="$1"
    local error_msg="$2"
    shift 2
    # Executing the command. Temporarily suppresses 'set -e' for this statement to allow graceful exit.
    if "$@"; then
        [ -n "$success_msg" ] && log_success "$success_msg"
    else
        [ -n "$error_msg" ] && log_error "$error_msg"
        exit 1
    fi
}

# Usage: assert_api "GET" "/endpoint" "200" "Success msg" "Error msg"
assert_api() {
    local method="$1"
    local endpoint="$2"
    local expected_status="$3"
    local success_msg="$4"
    local error_msg="$5"
    local status

    status=$(_api_status "$method" "$endpoint")
    if [[ "$status" == "$expected_status" ]]; then
        [ -n "$success_msg" ] && log_success "$success_msg"
    else
        [ -n "$error_msg" ] && log_error "$error_msg (HTTP $status)"
        exit 1
    fi
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

_redis_ping() {
    _redis ping | grep -q "PONG"
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

# Usage: _api_get "/endpoint"
_api_get() {
    curl -X 'GET' "${API_BASE_URL}$1" -H 'accept: application/json'
}

# Usage: _api_post "/endpoint" '{"json": "data"}'
_api_post() {
    # Hide raw output by piping to /dev/null but retain curl's exit code for assertion checking
    curl -s -o /dev/null -X 'POST' "${API_BASE_URL}$1" \
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

    status=$(curl -s -w "%{http_code}" -X 'GET' "${API_BASE_URL}$1" -o "$out_dir/$2")
    curl_exit=$?

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
    echo -e "  19) $(opt "stack")       Full Docker Stack        20) $(opt "down")        Stop Environment"

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
        20|stack)    run_script "docker-down" ;;
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
            assert_cmd "UV environment synchronised" "UV sync failed" uv sync --all-groups

            log_info "Installing pre-commit hooks..."
            assert_cmd "Git hooks active" "Failed to install pre-commit hooks" uv run pre-commit install

            log_info "Updating pre-commit hooks..."
            assert_cmd "Pre-commit hooks updated" "Failed to update hooks" uv run pre-commit autoupdate

            exec_cmd "lock"
            log_success "Packages installed successfully."
            ;;

        "lock")
            header "LOCKFILE SYNCHRONISATION"
            log_info "Updating UV lock..."
            assert_cmd "uv.lock upgraded to LTS" "Lock upgrade failed" uv lock --upgrade

            log_info "Checking lockfile integrity..."
            assert_cmd "Lockfile check passed" "Lockfile integrity check failed" uv lock --check

            if ask_yes_no "Would you like to view the dependency tree?"; then
                uv tree --all-groups
            fi

            log_info "Exporting dependencies to requirements.txt..."
            assert_cmd "Lockfiles updated successfully." "Export failed" uv export --format requirements.txt --output-file requirements.txt
            ;;

        "lint")
            header "LINTING & FORMATTING"
            log_info "Updating pre-commit hooks..."
            assert_cmd "Pre-commit hooks updated" "Pre-commit autoupdate failed" uv run pre-commit autoupdate

            log_info "Running Ruff..."
            assert_cmd "Ruff finished" "Ruff found issues" uv run ruff check --fix .

            log_info "Running Black..."
            assert_cmd "Black finished" "Black formatting failed" uv run black .

            log_info "Running Mypy..."
            assert_cmd "Mypy checks passed" "Mypy found type errors" uv run mypy .

            log_info "Running Pre-commit hooks..."
            assert_cmd "Linting complete." "Pre-commit hooks failed" uv run pre-commit run --all-files
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
                    assert_cmd "UV cache pruned" "Failed to prune UV cache" uv cache prune --force
                else
                    log_warn "UV not found, skipping cache prune..."
                fi

                log_info "Pruning Docker system..."
                assert_cmd "Docker artifacts cleaned" "Docker prune failed" docker builder prune -f

                log_info "Flushing Redis Cache..."
                if docker ps --format '{{.Names}}' | grep -q "^green-fintech-cache$"; then
                    assert_cmd "Redis cache cleared" "Failed to clear Redis" _redis FLUSHALL
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
            assert_cmd "Container started" "Failed to start Postgres container" _compose_build_up postgres

            log_info "Starting postgres database..."
            assert_cmd "PostgreSQL is active." "PostgreSQL script failed" ./scripts/db-helper.sh start

            assert_cmd "Seeding successful" "Database seeding failed" exec_cmd "db-seed"
            log_success "Postgres service is running successfully."
            ;;

        "seed"|"db-seed")
            header "POSTGRES DB INITIALISATION"
            log_info "Starting PostgreSQL Database..."
            assert_cmd "PostgreSQL is active." "Database failed to start" ./scripts/db-helper.sh start

            exec_cmd "mig-new"
            exec_cmd "mig-up"

            log_warn "Waiting for PostgreSQL to commit DDL changes..."
            sleep 2

            log_info "Seeding data..."
            assert_cmd "Seeds planted" "Database seeding failed" uv run python -m scripts.seed_db
            log_success "Postgres db fully initialised."
            ;;

        "db-stat")
            header "DATABASE INSPECTION"
            log_info "Starting PostgreSQL Database..."
            assert_cmd "PostgreSQL is active." "Failed to connect to database" ./scripts/db-helper.sh start

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
                assert_cmd "Environment wiped" "Failed to wipe environment" _compose_down -v

                if ask_yes_no "Would you like to purge Alembic history?"; then
                    rm -rf alembic/versions/*.py
                    log_success "Alembic history purged"
                fi

                if ask_yes_no "Would you like to run 'db-up'?"; then
                    exec_cmd "db-up"
                fi
            fi
            ;;

        "rd-up")
            header "REDIS SERVICE CREATION"
            log_info "Spinning up Redis container..."
            assert_cmd "Redis container running" "Failed to spin up Redis" _compose_build_up redis

            log_info "Pinging Redis..."
            assert_cmd "Redis is alive" "Redis unreachable" _redis_ping
            log_success "Redis service is running successfully."
            ;;

        "rd-stat")
            header "REDIS STATUS"
            log_info "Pinging Redis..."
            assert_cmd "Redis is alive" "Redis unreachable" _redis_ping

            log_info "Number of existing keys..."
            _redis DBSIZE

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
            assert_cmd "Ingestion complete." "Ingestion failed" _api_post "/api/v1/companies/" '{"company_number": "01026167"}'

            log_info "7. Checking Redis Keys (The 'companies:csv' key should be purged):"
            _redis KEYS "*"

            log_info "8. Re-caching the CSV file..."
            curl -s -o /dev/null -X 'GET' "${API_BASE_URL}/api/v1/companies/export/csv"

            log_info "9. Triggering DELETE invalidation (Removing Company ID 2)..."
            assert_cmd "Deletion complete." "Deletion failed" _api_delete "/api/v1/companies/2"

            log_info "10. Final Redis Keys (The 'companies:csv' key should be purged again):"
            _redis KEYS "*"
            log_success "Cache behavior diagnostics complete."
            ;;

        "mig-new")
            header "NEW MIGRATION"
            assert_cmd "PostgreSQL is active." "Database unavailable" ./scripts/db-helper.sh start

            log_info "Generating migration script..."
            read -p "Enter migration message: " msg
            if [ -n "$msg" ]; then
                uv run alembic revision --autogenerate -m "$msg" && log_success "Migration created in ./alembic/versions"
            else
                log_error "Migration message cannot be empty."
                exit 1
            fi
            ;;

        "mig-up")
            header "UPGRADING SCHEMA"
            log_info "Readying to apply..."
            read -p "Enter migration tag (optional): " tag
            if [ -n "$tag" ]; then
                assert_cmd "Migration applied successfully." "Migrations failed" uv run alembic upgrade head --tag "$tag"
            else
                assert_cmd "Migration applied successfully." "Migrations failed" uv run alembic upgrade head
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
                assert_cmd "Rollback complete" "Rollback failed" uv run alembic downgrade "-$rev"
            else
                log_info "Skipping rollback..."
            fi
            log_success "Migration status check complete."
            ;;

        "api-up")
            if ask_yes_no "Would you like to run 'kill-ports'?"; then exec_cmd "kill-ports"; fi

            header "FASTAPI SERVICE CREATION"
            log_info "Spinning up FastAPI container..."
            assert_cmd "Container started" "Failed to start FastAPI container" _compose_build_up api

            log_info "Waiting for API readiness..."
            sleep 5

            assert_api "GET" "/health" "200" "API Health OK" "Health check failed"
            log_success "FastAPI service is running successfully."
            ;;

        "api-stat")
            header "FASTAPI STATUS"
            log_info "Checking Health Endpoint..."
            assert_api "GET" "/health" "200" "Health OK" "Health check failed"

            log_info "Checking OpenAPI Docs..."
            assert_api "GET" "/docs" "200" "Docs OK" "Docs unreachable"

            log_info "Checking OpenAPI Docs..."
            assert_api "GET" "/redoc" "200" "Redocs OK" "Redocs unreachable"

            log_info "Ingesting TESCO PLC (00445790)..."
            assert_cmd "Ingestion successful" "Tesco ingestion failed" _api_post "/api/v1/companies/" '{"company_number": "00445790"}'
            echo

            log_info "Ingesting SHELL PLC (04366849)..."
            assert_cmd "Ingestion successful" "Shell ingestion failed" _api_post "/api/v1/companies/" '{"company_number": "04366849"}'
            echo

            log_info "Simulating Green Loan (Tesco)..."
            assert_cmd "Ingestion successful" "Simulation failed" _api_post "/api/v1/companies/1/simulate-loan" '{"loan_amount": 1000000, "term_months": 120}'
            echo

            log_info "Testing CSV Bulk Export..."
            assert_cmd "CSV Exported successfully to companies_export.csv" "CSV Export failed" _api_download "/api/v1/companies/export/csv" "companies_export.csv"

            log_info "Testing PDF Quote Generation..."
            assert_cmd "PDF Rendered successfully to green_loan_quote.pdf" "PDF Generation failed" _api_download "/api/v1/companies/1/simulate-loan/1/pdf" "green_loan_quote.pdf"

            log_info "Checking container logs..."
            _compose_logs api
            log_success "FastAPI status check complete."
            ;;

        "run")
            if ask_yes_no "Would you like to run 'kill-ports'?"; then exec_cmd "kill-ports"; fi

            header "LOCAL FASTAPI SERVER"
            # TODO: Extend redis caching for local hosting.
            log_info "Starting Uvicorn..."
            uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
            ;;

        "test")
            if ask_yes_no "Would you like to run 'kill-ports'?"; then exec_cmd "kill-ports"; fi
            log_info "Wiping containers and volumes..."
            assert_cmd "Environment wiped" "Failed to clear test environment" _compose_down --remove-orphans -v

            header "RUNNING TEST SUITE"
            if ask_yes_no "Run with coverage report?"; then
                log_info "Running tests with coverage report..."
                assert_cmd "Coverage report generated in htmlcov/index.html" "Tests failed." uv run pytest --cov=src --cov-report=html

                log_info "Opening coverage report in browser..."
                xdg-open htmlcov/index.html
            else
                log_info "Running tests (standard mode)..."
                assert_cmd "Tests passed" "Tests failed." uv run pytest -v
            fi

            if ask_yes_no "View specific tests in debug mode?"; then
                read -p "Specify the marker(s): " markers
                assert_cmd "Tests passed" "Tests failed." uv run pytest -m "$markers" -v --log-cli-level=DEBUG
            fi

            if ask_yes_no "Run specific test file or directory?"; then
                read -p "Enter test file or directory within tests/ (e.g., db_test.py): " test_path
                assert_cmd "Tests passed" "Tests failed." uv run pytest -v "$test_path"
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
            assert_cmd "Environment wiped" "Failed to stop containers" _compose_down --remove-orphans -v

            if ask_yes_no "Would you like to clear Docker artifacts?"; then
                assert_cmd "Docker artifacts cleaned" "Prune failed" docker builder prune -f
            fi

            log_info "Building and starting all services..."
            if ask_yes_no "Would you like to build the containers from scratch?"; then
                assert_cmd "Stack built from scratch" "Stack failed to start." _compose_build_up
                assert_cmd "Database seeded" "Database failed to initialize." exec_cmd "db-seed"
            else
                assert_cmd "Stack up and running" "Stack failed to start." _compose_up
                if ask_yes_no "Would you like to reinitialise the database?"; then
                    assert_cmd "Database seeded" "Database failed to initialize." exec_cmd "db-seed"
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
            assert_cmd "Environment stopped" "Failed to stop environment" _compose_down
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
