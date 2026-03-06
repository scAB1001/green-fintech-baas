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

# --- UI Helpers ---
log_success() { echo -e " ${GREEN}${BOLD}✓${NC} ${GREEN}$1${NC}"; }
log_error()   { echo -e " ${RED}${BOLD}✗${NC} ${RED}$1${NC}"; }
log_info()    { echo -e " ${BLUE}${BOLD}i${NC} ${BLUE}$1${NC}"; }
log_warn()    { echo -e " ${YELLOW}${BOLD}⚠${NC} ${YELLOW}$1${NC}"; }
header()      { echo -e "\n${PURPLE}${BOLD}=========== $1 ===========${NC}"; }
opt()         { echo -ne "${NC}${BOLD}[${BLUE}$1${NC}${BOLD}]${NC}"; }

# Load environment variables from .env
load_env() {
    # Docker configurations
    export COMPOSE_DOCKER_CLI_BUILD=1
    export DOCKER_BUILDKIT=1

    # VM configurations
    sudo sysctl vm.swappiness=1
    sudo sysctl vm.overcommit_memory=1

    if [ -f .env ]; then
        # Read .env line by line, ignoring comments and empty lines
        while IFS= read -r line || [ -n "$line" ]; do
            if [[ ! "$line" =~ ^\s*# ]] && [[ -n "$line" ]]; then
                clean_line=$(echo "$line" | sed 's/\s*#.*$//' | tr -d '\r')
                export "$clean_line"
            fi
        done < .env
    else
        log_warn "No .env file found, using defaults"
        export POSTGRES_USER="postgres"
        export POSTGRES_PASSWORD="postgres"
        export POSTGRES_DB="green_fintech"
        export POSTGRES_PORT=5432
        export POSTGRES_INITDB_ARGS="--auth=scram-sha-256"
    fi
}

# --- Standard wrappers for Redis commands ---
_redis() {
    docker exec -e REDISCLI_AUTH="${REDIS_PASSWORD}" green-fintech-cache redis-cli "$@"
}

_redis_it() {
    docker exec -e REDISCLI_AUTH="${REDIS_PASSWORD}" -it green-fintech-cache redis-cli "$@"
}

# --- Interactive Menu ---
show_menu() {
    clear

    # Fallback to UV CLI cache size or simple cache string
    local uv_cache_info="N/A"
    if command -v uv >/dev/null 2>&1; then
        uv_cache_info=$(uv cache size --preview-features cache-size 2>/dev/null || echo "Unknown")
    fi

    echo -e "${CYAN}${BOLD}🍃 Green FinTech BaaS - Interactive CLI${NC}      ${YELLOW}UV Cache:${NC} $uv_cache_info"
    echo -e "-------------------------------------------------------------------------------------"

    echo -e "${BOLD}🛠️  Core Setup & Maintenance${NC}"
    echo -e "  01) $(opt "init")        Full Install (UV)        02) $(opt "lock")        Regen Lockfiles"
    echo -e "  03) $(opt "lint")        Ruff/Black/Mypy          04) $(opt "clean")       Deep Workspace Purge"
    echo -e "  05) $(opt "kill")        Kill Ports 8000 & 8080"

    echo -e "\n${BOLD}🐘 Postgres Database (Local/Docker)${NC}"
    echo -e "  06) $(opt "db-up")       Start PG Container       07) $(opt "db-init")     Seed PG"
    echo -e "  08) $(opt "db-stat")     Health & Stats           09) $(opt "db-psql")     Interactive Shell"
    echo -e "  10) $(opt "db-sql")      Interactive Shell        11) $(opt "db-wipe")     Nuke Volumes & Reset"

    echo -e "\n${BOLD}🚀 Redis Cache Service${NC}"
    echo -e "  12) $(opt "rd-up")       Start Redis Container    13) $(opt "rd-stat")     Ping & Key Check"
    echo -e "  14) $(opt "rd-cli")      Interactive CLI"

    echo -e "\n${BOLD}⚗️  uv run Alembic Migrations${NC}"
    echo -e "  15) $(opt "mig-new")     Create Autogen Rev       16) $(opt "mig-up")      Preview & Apply"
    echo -e "  17) $(opt "mig-stat")    History & Rollback"

    echo -e "\n${BOLD}🌐 FastAPI Service${NC}"
    echo -e "  18) $(opt "api-up")      Start FastAPI Container  19) $(opt "api-stat")    Health/Docs/Endpoint"
    echo -e "  20) $(opt "run")         Local Uvicorn Server"

    echo -e "\n${BOLD}🌐 Testing, Building and Publishing${NC}"
    echo -e "  21) $(opt "stack")       Full Docker Stack        22) $(opt "down")        Stop Containers"
    echo -e "  23) $(opt "test")        Pytest (Standard)        24) $(opt "cov")         Pytest (XML Coverage)"
    echo -e "  25) $(opt "build")       Package for [Test]PyPI   26) $(opt "publish")     Publish to [Test]PyPI"

    echo -ne "\n   q) ${NC}[${RED}Quit${NC}]        ${YELLOW}Select an option: ${NC}"

    read -r opt

    # Normalise to lower()
    opt=$(echo "$opt" | tr '[:upper:]' '[:lower:]')

    case $opt in
        1|init)      run_script "init" ;;
        2|lock)      run_script "lock" ;;
        3|lint)      run_script "lint" ;;
        4|clean)     run_script "clean" ;;
        5|kill)      run_script "kill-ports" ;;
        6|db-up)     run_script "db-up" ;;
        7|db-init)   run_script "db-init" ;;
        8|db-stat)   run_script "db-stat" ;;
        9|db-psql)   run_script "db-psql" ;;
        10|db-sql)   run_script "db-sql" ;;
        11|db-wipe)  run_script "db-wipe" ;;
        12|rd-up)    run_script "rd-up" ;;
        13|rd-stat)  run_script "rd-stat" ;;
        14|rd-cli)   run_script "rd-cli" ;;
        15|mig-new)  run_script "mig-new" ;;
        16|mig-up)   run_script "mig-up" ;;
        17|mig-stat) run_script "mig-stat" ;;
        18|api-up)   run_script "api-up" ;;
        19|api-stat) run_script "api-stat" ;;
        20|run)      run_script "run" ;;
        21|stack)    run_script "docker-stack" ;;
        22|down)     run_script "docker-down" ;;
        23|test)     run_script "test" ;;
        24|cov)      run_script "test" "cov" ;;
        25|build)    run_script "build" ;;
        26|publish)  run_script "publish" ;;
        q|quit|exit) log_success "Exiting..."; exit 0 ;;
        *)  log_error "Invalid option"; sleep 1; show_menu ;;
    esac
}

# --- Command Logic ---
exec_cmd() {
    case "$1" in
        "init")
            header "INITIALISING PROJECT"
            # uv reads pyproject.toml, creates the venv, and installs everything
            log_info "Syncing UV environment and installing all groups..."
            uv sync --all-groups && log_success "UV environment synchronised"

            log_info "Installing pre-commit hooks..."
            uv run pre-commit install && log_success "Git hooks active"
            ;;

        "lock")
            header "LOCKFILE SYNCHRONISATION"
            log_info "Updating UV lock..."
            uv lock --upgrade && log_success "uv.lock upgraded to LTS"

            log_info "Checking lockfile integrity..."
            uv lock --check

            log_info "Displaying dependency tree..."
            uv tree

            log_success "Lockfiles updated successfully."
            ;;

        "db-up")
            header "POSTGRES SERVICE CREATION"
            log_info "Spinning up Postgres container..."
            $COMPOSE_CMD up --build -d postgres && log_success "Container started"

            log_info "Starting postgres database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            exec_cmd "db-init"
            log_success "Postgres service is running successfully."
            ;;

        "db-init")
            header "POSTGRES DB INITIALISATION"
            log_info "Applying migrations..."
            uv run alembic upgrade head && log_success "Schema up to date"

            log_info "Seeding data..."
            python scripts/seed_db.py && log_success "Seeds planted"
            log_success "Postgres db fully initialised."
            ;;

        "db-stat")
            header "DATABASE INSPECTION"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            # Call the aggregated inspection command
            ./scripts/db-helper.sh inspect

            log_info "Checking container logs..."
            $COMPOSE_CMD logs --tail=20 postgres
            log_success "Postgres status check complete."
            ;;

        "db-wipe")
            header "DATABASE PURGE"
            log_warn "This will delete all persistent data in Postgres!"
            read -p "Are you sure? (y/n): " confirm
            if [[ $confirm == "y" || $confirm == "Y" ]]; then
                log_info "Stopping containers and removing volumes..."
                $COMPOSE_CMD down -v && log_success "Environment wiped"
                exec_cmd "db-up"
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

            log_info "Connecting to green-fintech-db..."
            ./scripts/db-helper.sh psql
            ;;

        "rd-up")
            header "REDIS SERVICE CREATION"
            log_info "Spinning up Redis container..."
            $COMPOSE_CMD up --build -d cache && log_success "Redis container running"

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

            log_info "Performing endpoint test with CURL..."
            curl -X 'GET' 'http://localhost:8080/api/v1/companies/1' -H 'accept: application/json'
            echo

            log_info "Checking for new keys..."
            _redis KEYS "*" | grep ":" && log_success "Data present" || log_error "Cache empty"

            log_info "Checking container logs..."
            $COMPOSE_CMD logs --tail=20 redis
            log_success "Redis status check complete."
            ;;

        "rd-cli")
            header "REDIS INTERACTIVE SHELL"
            log_info "Connecting to green-fintech-cache..."
            _redis_it
            ;;

        "mig-new")
            header "NEW MIGRATION"
            log_info "Starting PostgreSQL Database..."
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
            read -p "Apply migration to database? (y/n): " apply
            if [[ "$apply" == "y" || "$apply" == "Y" ]]; then
                read -p "Enter migration tag (optional): " tag
                if [ -n "$tag" ]; then
                    uv run alembic upgrade head --tag "$tag"
                else
                    uv run alembic upgrade head
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
            exec_cmd "kill-ports"

            header "FASTAPI SERVICE CREATION"
            log_info "Spinning up FastAPI container..."
            $COMPOSE_CMD up --build -d api && log_success "Container started"

            log_info "Waiting for API readiness..."
            sleep 5

            log_info "Performing health test with CURL..."
            curl -s 'http://localhost:8080/health' || log_error "Health check failed"
            echo
            log_success "FastAPI service is running successfully."
            ;;

        "api-stat")
            header "FASTAPI STATUS"
            log_info "Performing health test with CURL..."
            curl -s -X 'GET' 'http://localhost:8080/health' -H 'accept: application/json' || log_error "Failed"
            echo

            log_info "Performing docs test with CURL..."
            curl -s -o /dev/null -w "%{http_code}" -X 'GET' 'http://localhost:8080/docs' -H 'accept: application/json' | grep -q "200" && log_success "Docs OK" || log_error "Docs unreachable"
            echo

            log_info "Checking container logs..."
            $COMPOSE_CMD logs --tail=20 api
            log_success "FastAPI status check complete."
            ;;

        "kill-ports")
            header "PORT KILLER"
            for port in 8000 8080; do
                log_info "Checking Port $port..."
                if lsof -i :$port -t >/dev/null ; then
                    log_warn "Port $port is already in use."
                    log_info "Killing process using port $port..."
                    sudo lsof -i :$port -t | xargs kill -9 2>/dev/null || true
                    log_success "Port $port is free"
                else
                    log_success "Port $port is free"
                fi
            done
            ;;

        "clean")
            header "WORKSPACE PURGE"
            log_warn "You are about to delete all cached files, build artifacts, and docker images."
            read -p "Proceed? (y/n): " proceed
            if [[ "$proceed" == "y" || "$proceed" == "Y" ]]; then
                log_info "Cleaning Python caches..."
                find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
                find . -type f -name "*.py[co]" -delete 2>/dev/null || true
                log_success "Pycache removed"

                log_info "Cleaning tool artifacts..."
                rm -rf .pytest_cache .coverage .mypy_cache .ruff_cache dist build *.egg-info 2>/dev/null || true
                log_success "Tool caches and environments purged"

                if command -v uv >/dev/null 2>&1; then
                    log_info "Cache Prune (UV)"
                    uv cache prune -v && log_success "UV cache removed"
                fi

                log_info "Pruning Docker system..."
                docker builder prune -f && log_success "Docker artifacts cleaned"

                log_info "Flushing Redis Cache..."
                if docker ps --format '{{.Names}}' | grep -q "^green-fintech-cache$"; then
                    $REDIS_CMD FLUSHALL && log_success "Redis cache cleared"
                fi
                log_success "Workspace cleaned."
            fi
            ;;

        "run")
            exec_cmd "kill-ports"

            header "LOCAL FASTAPI SERVER"
            log_info "Starting Uvicorn..."
            uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
            ;;

        "docker-stack")
            read -p "Would you like to run 'kill-ports'? (y/n): " kill_ports
            if [[ "$kill_ports" == "y" || "$kill_ports" == "Y" ]]; then
                exec_cmd "kill-ports"
            fi
            read -p "Would you like to run 'lock'? (y/n): " lock
            if [[ "$lock" == "y" || "$lock" == "Y" ]]; then
                exec_cmd "lock"
            fi

            header "DOCKER COMPOSE STACK"
            log_info "Clearing space..."
            $COMPOSE_CMD down -v && log_success "Environment wiped"

            read -p "Would you like to clear Docker artifacts? (y/n): " prune
            if [[ "$prune" == "y" || "$prun" == "Y" ]]; then
                docker builder prune -f && log_success "Docker artifacts cleaned"
            fi

            log_info "Building and starting all services..."
            read -p "Would you like to builder the container from scratch? (y/n): " scratch
            if [[ "$scratch" == "y" || "$scratch" == "Y" ]]; then
                $COMPOSE_CMD up --build -d || { log_error "Stack failed to start."; exit 1; }
            else
                $COMPOSE_CMD up -d || { log_error "Stack failed to start."; exit 1; }
            fi
            log_success "Stack running in background"

            log_info "Initialising database..."
            exec_cmd "db-init" || { log_error "Database failed to initialize."; exit 1; }

            log_info "Service Status"
            $COMPOSE_CMD ps

            sleep 2 && exec_cmd "db-stat"
            sleep 2 && exec_cmd "mig-stat"
            sleep 2 && exec_cmd "api-stat"
            sleep 2 && exec_cmd "rd-stat"

            log_success "Docker stack status check complete."
            ;;

        "docker-down")
            header "DOCKER COMPOSE DOWN"
            log_info "Viewing existing processes..."
            $COMPOSE_CMD ps

            log_info "Stopping Containers..."
            $COMPOSE_CMD down && log_success "Environment stopped"
            ;;

        "test")
            header "RUNNING TEST SUITE"
            if [ "$2" == "cov" ]; then
                log_info "Running tests with coverage report..."
                uv run pytest --cov=src --cov-report=xml && log_success "Coverage report generated in coverage.xml"
            else
                log_info "Running tests (standard mode)..."
                uv run pytest -v && log_success "Tests passed" || log_error "Tests failed"
            fi

            # DEBUG: pytest -v --log-cli-level=DEBUG
            # TODO: Add marker test options for "slow", "db", "api", etc. (pytest -m integration)
            # read -p "View test coverage report? (y/n): " view_cov
            # if [[ "$view_cov" == "y" ]]; then
            #     pytest --cov=src --cov-report=html
            #     log_info "Opening coverage report in browser..."
            #     xdg-open htmlcov/index.html
            # fi

            # TODO: Add further specific test file or directory options (pytest -s tests/db_test.py)
            # read -p "Run specific test file or directory? (y/n): " run_specific
            # if [[ "$run_specific" == "y" ]]; then
            #     read -p "Enter test file or directory within tests/ (e.g., db_test.py): " test_path
            #     pytest -v "$test_path"
            # fi
            ;;

        "lint")
            header "LINTING & FORMATTING"
            log_info "Updating pre-commit hooks..."
            uv run pre-commit autoupdate && log_success "Pre-commit hooks updated"

            log_info "Running Ruff (Fix)..."
            uv run ruff check --fix . && log_success "Ruff finished"

            log_info "Running Black..."
            uv run black . && log_success "Black finished"

            log_info "Running Mypy..."
            uv run mypy . && log_success "Mypy checks passed"

            log_info "Running Pre-commit hooks..."
            uv run pre-commit run --all-files
            log_success "Linting complete."
            ;;

        "build")
            header "PACKAGING FOR PYPI"
            log_info "Cleaning old build artifacts..."
            rm -rf dist/ build/ *.egg-info

            log_info "Building wheel and sdist with UV..."
            uv build && log_success "Build artifacts created in dist/"
            ;;

        "publish")
            header "PUBLISHING TO TEST PYPI"
            # log_info "Configuring repository..."
            # config repositories.testpypi https://test.pypi.org/legacy/ || true

            log_info "Uploading package using Twine via UV..."
            # Twine reads TWINE_USERNAME and TWINE_PASSWORD from your environment (.env)
            # If not set, it will prompt you securely in the terminal.
            uv run twine upload --repository testpypi dist/* --verbose
            ;;

        *)
            log_error "Command '$1' not found."
            ;;
    esac
}

# --- Interactive Wrapper ---
run_script() {
    # Extract arg[0] and set local var to lower()
    local cmd=$(echo "$1" | tr '[:upper:]' '[:lower:]')

    # Rm the old arg[0]
    shift

    # Run new cmd, passing along any extra args ($@)
    exec_cmd "$cmd" "$@"

    echo -e "\n${YELLOW}Press enter to return to menu...${NC}"
    read -r
    show_menu
}

# --- Execution Entry ---
# Load the environment variables first
load_env
if [ -z "$1" ]; then
    show_menu
else
    # Usage: `./exec.sh db-up` - exits cleanly without trapping them in the menu
    # Extract arg[0] and convert to lower()
    cmd=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    shift
    exec_cmd "$cmd" "$@"
fi
