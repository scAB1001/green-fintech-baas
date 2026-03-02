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

# --- UI Helpers ---
log_success() { echo -e " ${GREEN}${BOLD}✓${NC} ${GREEN}$1${NC}"; }
log_error()   { echo -e " ${RED}${BOLD}✗${NC} ${RED}$1${NC}"; }
log_info()    { echo -e " ${BLUE}${BOLD}i${NC} ${BLUE}$1${NC}"; }
log_warn()    { echo -e " ${YELLOW}${BOLD}⚠${NC} ${YELLOW}$1${NC}"; }
header()      { echo -e "\n${PURPLE}${BOLD}=========== $1 ===========${NC}"; }
opt()         { echo -ne "${NC}${BOLD}[${BLUE}$1${NC}${BOLD}]${NC}"; }

# --- Interactive Menu ---
show_menu() {
    clear

    echo -e "${CYAN}${BOLD}🍃 Green FinTech BaaS - Interactive CLI${NC}"
    echo -e "${YELLOW}Poetry:${NC} $(poetry env info --path 2>/dev/null || echo 'None')"
    echo -e "${YELLOW}UV Cache:${NC} $(uv cache size --preview-features cache-size 2>/dev/null || echo 'N/A')"
    echo -e "-------------------------------------------------------------------------"

    echo -e "${BOLD}🛠️  Core Setup & Maintenance${NC}"
    echo -e "  01) $(opt "init")        Full Install (Both)      02) $(opt "lock")        Regen Lockfiles"
    echo -e "  03) $(opt "lint")        Ruff/Black/Mypy          04) $(opt "clean")       Deep Workspace Purge"
    echo -e "  05) $(opt "kill")        Kill Ports 8000 & 8080"

    echo -e "\n${BOLD}🐘 Postgres Database (Local/Docker)${NC}"
    echo -e "  06) $(opt "db-up")       Start & Seed PG          07) $(opt "db-stat")     Health & Stats"
    echo -e "  08) $(opt "db-psql")     Interactive Shell        09) $(opt "db-sql")      Run Custom Query"
    echo -e "  10) $(opt "db-wipe")     Nuke Volumes & Reset"

    echo -e "\n${BOLD}🚀 Redis Cache Service${NC}"
    echo -e "  11) $(opt "rd-up")       Start Redis Container    12) $(opt "rd-stat")     Ping & Key Check"
    echo -e "  13) $(opt "rd-cli")      Interactive CLI"

    echo -e "\n${BOLD}⚗️  Alembic Migrations${NC}"
    echo -e "  14) $(opt "mig-new")     Create Autogen Rev       15) $(opt "mig-up")      Preview & Apply"
    echo -e "  16) $(opt "mig-stat")    History & Rollback"

    echo -e "\n${BOLD}🌐 FastAPI Service${NC}"
    echo -e "  17) $(opt "api-up")      Docker API Container     18) $(opt "api-stat")    Health/Docs/Endpoint"
    echo -e "  19) $(opt "run")         Local Uvicorn Server"

    echo -e "\n${BOLD}🌐 Testing, Building and Publishing${NC}"
    echo -e "  20) $(opt "stack")       Full Docker Stack"
    echo -e "  21) $(opt "test")        Pytest (Standard)        22) $(opt "cov")         Pytest (XML Coverage)"
    echo -e "  23) $(opt "build")       Package for [Test]PyPI   24) $(opt "publish")     Publish to [Test]PyPI"

    echo -e "\n   q) ${NC}[${RED}Quit${NC}]"
    echo -ne "\n${YELLOW}Select an option: ${NC}"
    read -r opt

    case $opt in
        1)  run_cmd "init" ;;
        2)  run_cmd "lock" ;;
        3)  run_cmd "lint" ;;
        4)  run_cmd "clean" ;;
        5)  run_cmd "kill-ports" ;;
        6)  run_cmd "db-up" ;;
        7)  run_cmd "db-status" ;;
        8)  run_cmd "db-psql" ;;
        9)  run_cmd "db-sql" ;;
        10) run_cmd "db-wipe" ;;
        11) run_cmd "rd-up" ;;
        12) run_cmd "rd-stat" ;;
        13) run_cmd "rd-cli" ;;
        14) run_cmd "mig-new" ;;
        15) run_cmd "mig-up" ;;
        16) run_cmd "mig-stat" ;;
        17) run_cmd "api-up" ;;
        18) run_cmd "api-stat" ;;
        19) run_cmd "run" ;;
        20) run_cmd "docker-stack" ;;
        21) run_cmd "test" ;;
        22) run_cmd "test" "cov" ;;
        23) run_cmd "build" ;;
        24) run_cmd "publish" ;;
        q)  exit 0 ;;
        *)  log_error "Invalid option"; sleep 1; show_menu ;;
    esac
}

# --- Command Logic ---
run_cmd() {
    case "$1" in
        "init")
            header "INITIALIZING PROJECT"
            # ----- POETRY -----
            log_info "Installing core deps via Poetry..."
            poetry add fastapi httpx pydantic pydantic-settings "sqlalchemy[asyncio]" asyncpg "psycopg[binary]" alembic uvicorn redis && log_success "Poetry core deps added" || log_error "Poetry core failed"

            log_info "Adding dev dependencies..."
            poetry add black isort ruff mypy pre-commit pytest pytest-cov pytest-asyncio --group dev && log_success "Dev tools added"

            log_info "Adding testing dependencies..."
            poetry add pytest pytest-cov pytest-asyncio pytest-docker --group test && log_success "Test tools added"

            log_info "Adding documentation dependencies..."
            poetry add sphinx --group docs && log_success "Doc tools added"

            log_info "Installing dependencies in current environment..."
            # --without test
            poetry install --with dev,test,docs && log_success "Dependency groups installed"

            # ----- UV -----
            log_info "Syncing UV environment..."
            uv pip install -e . && log_success "UV environment synchronized"

            log_info "Installing pre-commit hooks..."
            pre-commit install && log_success "Git hooks active"
            ;;

        "lock")
            header "LOCKFILE SYNCHRONIZATION"
            # ----- POETRY -----
            log_info "Updating Poetry lock..."
            poetry lock --regenerate && log_success "poetry.lock upgraded to LTS"

            log_info "Checking lockfile integrity..."
            poetry check --lock --strict

            log_info "Re-installing dependencies in current environment..."
            poetry install && log_success "Dependencies reinstalled."

            # log_info "Exporting all dependencies to requirements.txt..."
            # poetry export -f requirements.txt --output requirements.txt --without-hashes --all-groups

            log_info "Displaying dependency tree..."
            poetry show --tree

            # ----- UV -----
            log_info "Updating UV lock..."
            uv lock --upgrade && log_success "uv.lock upgraded to LTS"

            log_info "Checking lockfile integrity..."
            uv lock --check

            # log_info "Exporting all dependencies to requirements.txt..."
            # uv export --format requirements.txt

            log_success "Lockfiles updated successfully."
            ;;

        "db-up")
            header "POSTGRES INITIALIZATION"
            log_info "Spinning up Postgres container..."
            docker compose up --build -d postgres && log_success "Container started"

            log_info "Waiting for PG readiness..."
            sleep 2

            log_info "Starting postgres database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            log_info "Applying migrations..."
            alembic upgrade head && log_success "Schema up to date"

            log_info "Seeding data..."
            python scripts/seed_db.py && log_success "Seeds planted"
            log_success "Postgres service is running successfully."
            ;;

        "db-status")
            header "DATABASE INSPECTION"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            log_info "Testing database access..."
            ./scripts/db-helper.sh test-access

            log_info "Showing configuration and runtime settings..."
            ./scripts/db-helper.sh config

            log_info "Checking active connections..."
            ./scripts/db-helper.sh connections

            log_info "Gathering database statistics..."
            ./scripts/db-helper.sh stats

            log_info "Listing tables and sizes..."
            ./scripts/db-helper.sh tables

            log_info "Checking container logs..."
            docker compose logs --tail=20 postgres
            log_success "Postgres status check complete."
            ;;

        "db-wipe")
            header "DATABASE PURGE"
            log_warn "This will delete all persistent data in Postgres!"
            read -p "Are you sure? (y/n): " confirm
            if [[ $confirm == "y" ]]; then
                log_info "Stopping containers and removing volumes..."
                docker compose down --remove-orphans  -v && log_success "Environment wiped"
                run_cmd "db-up"
            fi
            ;;

        "db-sql")
            header "RUNNING CUSTOM SQL"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            # TODO: Implement helpful queries
            # ./scripts/db-helper.sh sql "SELECT id, name FROM companies;"

            # "\dt", "SELECT * FROM alembic_version;", "\di"
            log_info "Enter a SQL query (e.g., \dt or SELECT * FROM table;)"
            read -p "Enter SQL query: " query
            ./scripts/db-helper.sh sql "$query"
            log_success "Query executed successfully."
            ;;

        "db-psql")
            header "POSTGRES INTERACTIVE SHELL"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            log_info "Connecting to green-fintech-db..."
            ./scripts/db-helper.sh psql

            # "\dt", "SELECT * FROM alembic_version;", "\di"
            log_success "Shell entered successfully."
            ;;

        "rd-up")
            header "REDIS MANAGEMENT"
            log_info "Spinning up Redis container..."
            docker compose up --build -d cache && log_success "Redis container running"

            # TODO: Don't use docker exec (replace)
            log_info "Pinging Redis..."
            docker exec -it green-fintech-cache redis-cli ping | grep "PONG" && log_success "Redis is alive" || log_error "Redis unreachable"

            log_info "Checking for existing keys"
            docker exec -it green-fintech-cache redis-cli KEYS "*" | grep ":" && log_success "Data present" || log_error "Cache empty"
            log_success "Redis service is running successfully."
            ;;

        "rd-stat")
            header "REDIS STATUS"
            log_info "Pinging Redis..."
            docker exec -it green-fintech-cache redis-cli ping | grep "PONG" && log_success "Redis is alive" || log_error "Redis unreachable"

            log_info "Checking for existing keys..."
            docker exec -it green-fintech-cache redis-cli KEYS "*" | grep ":" && log_success "Data present" || log_error "Cache empty"

            log_info "Performing endpoint test with CURL..."
            curl -X 'GET' 'http://localhost:8080/api/v1/companies/1' -H 'accept: application/json'
            echo "\n"

            log_info "Checking for new keys..."
            docker exec -it green-fintech-cache redis-cli KEYS "*" | grep ":" && log_success "Data present" || log_error "Cache empty"

            log_info "Checking container logs..."
            docker compose logs --tail=20 redis
            log_success "Redis status check complete."
            ;;

        "rd-cli")
            header "REDIS INTERACTIVE SHELL"
            log_info "Connecting to green-fintech-cache..."
            # TODO: Add docker exec commands in db-helper script or similar
            docker exec -it green-fintech-cache redis-cli
            log_success "Shell entered successfully."
            ;;

        "mig-new")
            header "NEW MIGRATION"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start && log_success "PostgreSQL is active."

            log_info "Generating migration script..."
            read -p "Enter migration message: " msg
            alembic revision --autogenerate -m "$msg" && log_success "Migration created in ./alembic/versions"
            ;;

        "mig-up")
            header "UPGRADING SCHEMA"
            log_info "Viewing generated migration script (SQL preview)..."
            alembic upgrade head --sql | tail -n 25

            log_info "Readying to apply..."
            read -p "Apply migration to database? (y/n) " apply
            if [[ "$apply" == "y" ]]; then
                read -p "Enter migration tag (optional): " tag
                alembic upgrade head --tag "$tag"
                log_success "Migration applied successfully."
            else
                log_warn "Migration not applied. Remember to apply it before running the app!"
            fi
            ;;

        "mig-stat")
            # TODO: Make history view and rollback interactive
            header "MIGRATION STATUS"
            log_info "Checking migration history..."
            alembic history --verbose | head -n 15

            # log_info View migration script revision history from X to current
            # alembic history -r6df59d73aea3: --verbose

            log_info "Rolling back to specified revision..."
            read -p "How many revisions/which revision would you like to rollback to? (y/n) " rev
            if [[ "$apply" == "y" ]]; then
                log_warn "Rolling back -$rev revision..."
                alembic downgrade -$rev && log_success "Rollback complete"
            else
                log_warn "Rollback failed"
            fi

            log_success "Migration status check complete."
            ;;

        "api-up")
            header "FASTAPI INITIALIZATION"
            log_info "Checking Port 8000..."
            if lsof -i :8000 -t >/dev/null ; then
                log_warn "Port 8000 is already in use."

                log_info "Killing process using port 8000..."
                sudo lsof -i :8000 -t | xargs kill -9 2>/dev/null || true
                log_success "Port 8000 is free"
            fi

            log_info "Spinning up FastAPI container..."
            docker compose up --build -d api && log_success "Container started"

            log_info "Waiting for API readiness..."
            sleep 2

            log_info "Performing health test with CURL..."
            curl -X 'GET' 'http://localhost:8080/health' -H 'accept: application/json'
            echo "\n"
            log_success "FastAPI service is running successfully."
            ;;

        "api-stat")
            header "FASTAPI STATUS"
            log_info "Performing health test with CURL..."
            curl -X 'GET' 'http://localhost:8080/health' -H 'accept: application/json'
            echo "\n"

            log_info "Performing docs test with CURL..."
            curl -X 'GET' 'http://localhost:8080/docs' -H 'accept: application/json'
            echo "\n"

            log_info "Performing endpoint test with CURL..."
            curl -X 'GET' 'http://localhost:8080/api/v1/companies/1' -H 'accept: application/json'
            echo "\n"

            log_info "Checking container logs..."
            docker compose logs --tail=20 api
            log_success "FastAPI status check complete."
            ;;

        "kill-ports")
            header "PORT KILLER"
            log_info "Checking Port 8000..."
            if lsof -i :8000 -t >/dev/null ; then
                log_warn "Port 8000 is already in use."

                log_info "Killing process using port 8000..."
                sudo lsof -i :8000 -t | xargs kill -9 2>/dev/null || true
                log_success "Port 8000 is free"
            fi

            log_info "Checking Port 8080..."
            if lsof -i :8080 -t >/dev/null ; then
                log_warn "Port 8080 is already in use."

                log_info "Killing process using port 8080..."
                sudo lsof -i :8080 -t | xargs kill -9 2>/dev/null || true
                log_success "Port 8080 is free"
            fi

            log_success "Ports 8000 and 8080 killed successfully."
            ;;

        "clean")
            # TODO: X files to be removed: successfully removed...
            header "WORKSPACE PURGE"

            # ----- LOCAL -----
            log_info "Cleaning Python caches..."
            find . -type d -name "__pycache__" -exec rm -rf {} +
            find . -type f -name "*.py[co]" -delete
            log_success "Pycache removed"

            log_info "Cleaning tool artifacts..."
            rm -rf .pytest_cache .coverage .mypy_cache .ruff_cache dist build *.egg-info
            log_success "Tool caches purged"

            # ----- UV -----
            # log_info "Cache Size"
            # uv cache size --preview-features cache-size -v

            # log_info "Cache Clean"
            # uv cache clean -v

            log_info "Cache Prune"
            uv cache prune -v && log_success "UV cache removed"

            # ----- DOCKER -----
            log_info "Pruning Docker system..."
            docker builder prune -f && log_success "Docker artifacts cleaned"

            log_info "Pruning Old Layers..."
            docker builder prune -a && log_success "Old layers cleaned"

            # ----- REDIS -----
            log_info "Flushing Redis Cache..."
            docker exec -it green-fintech-cache redis-cli FLUSHALL && log_success "Redis cache cleared"
            log_success "Workspace cleaned."
            ;;

        "run")
            header "LOCAL FASTAPI SERVER"
            log_info "Ensuring port 8000 is clear..."
            fuser -k 8000/tcp || true

            log_info "Starting Uvicorn..."
            uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
            ;;

        "docker-stack")
            header "DOCKER COMPOSE STACK"
            log_info "Clearing space"
            docker compose down --remove-orphans  -v && log_success "Environment wiped"
            docker exec -it green-fintech-cache redis-cli FLUSHALL && log_success "Redis cache cleared"
            docker builder prune -f && log_success "Docker artifacts cleaned"
            docker builder prune -a && log_success "Old layers cleaned"
            if lsof -i :8000 -t >/dev/null ; then
                sudo lsof -i :8000 -t | xargs kill -9 2>/dev/null || true
            fi
            if lsof -i :8080 -t >/dev/null ; then
                sudo lsof -i :8080 -t | xargs kill -9 2>/dev/null || true
            fi
            log_success "Ports free"

            log_info "Building and starting all services..."
            docker compose up --build -d && log_success "Stack running in background"

            log_info "Service Status:"
            docker compose logs
            docker compose ps
            ./scripts/db-helper.sh connections
            docker exec -it green-fintech-cache redis-cli ping
            docker exec -it green-fintech-cache redis-cli KEYS "*"
            curl -X 'GET' 'http://localhost:8080/health' -H 'accept: application/json'
            echo "\n"
            curl -X 'GET' 'http://localhost:8080/api/v1/companies/1' -H 'accept: application/json'
            echo "\n"
            docker exec -it green-fintech-cache redis-cli KEYS "*"

            log_success "Docker stack status check complete."
            ;;

        "test")
            header "RUNNING TEST SUITE"
            if [ "$2" == "cov" ]; then
                log_info "Running tests with coverage report..."
                pytest --cov=src --cov-report=xml && log_success "Coverage report generated in xmlcov/"
            else
                log_info "Running tests (standard mode)..."
                pytest -v && log_success "Tests passed" || log_error "Tests failed"
            fi

            # EEEBUG: pytest -v --log-cli-level=DEBUG
            # TODO: Add marker test options for "slow", "db", "api", etc. (pytest -m integration)
            # read -p "View test coverage report? (y/n) " view_cov
            # if [[ "$view_cov" == "y" ]]; then
            #     pytest --cov=src --cov-report=html
            #     log_info "Opening coverage report in browser..."
            #     xdg-open htmlcov/index.html
            # fi

            # TODO: Add further specific test file or directory options (pytest -s tests/db_test.py)
            # read -p "Run specific test file or directory? (y/n) " run_specific
            # if [[ "$run_specific" == "y" ]]; then
            #     read -p "Enter test file or directory within tests/ (e.g., db_test.py): " test_path
            #     pytest -v "$test_path"
            # fi
            ;;

        "lint")
            header "LINTING & FORMATTING"
            log_info "Updating pre-commit hooks..."
            pre-commit autoupdate && log_success "Pre-commit hooks updated"

            log_info "Showing unsafe fixes..."
            ruff check --unsafe-fixes src/ tests/ || true

            log_info "Running Ruff (Fix)..."
            ruff check --fix . --show-diff-on-failure && log_success "Ruff finished"

            # log_info "Ruff enforce check for F401 and F403 rules..."
            # ruff check src/ tests/ --select F401,F403
            # log_success "Rules F401 and F403 enforced"

            log_info "Running Black..."
            black . && log_success "Black finished"

            log_info "Running Mypy..."
            mypy . && log_success "Mypy checks passed"

            log_info "Running Pre-commit hooks..."
            pre-commit run --all-files --verbose
            log_success "Linting complete."
            ;;

        "build")
            header "PACKAGING FOR PYPI"
            log_info "Cleaning old build artifacts..."
            rm -rf dist/ build/ *.egg-info

            log_info "Building wheel and sdist with Poetry..."
            poetry build

            log_info "Building wheel and sdist with UV..."
            uv build

            log_success "Build artifacts created in dist/"
            ;;

        "publish")
            header "PUBLISHING TO TEST PYPI"
            # poetry config http-basic.pypi <user> <pass>
            # poetry config pypi-token.testpypi <token>
            log_info "Configuring repository..."
            poetry config repositories.testpypi https://test.pypi.org/legacy/

            log_info "Uploading package..."
            twine upload --repository testpypi dist/* --verbose
            ;;

        *)
            show_menu
            ;;
    esac

    echo -e "\n${YELLOW}Press enter to return to menu...${NC}"
    read -r
    show_menu
}

# --- Execution Entry ---
if [ -z "$1" ]; then
    show_menu
else
    run_cmd "$@"
fi
