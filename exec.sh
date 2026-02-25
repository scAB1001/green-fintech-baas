#!/bin/bash


# --- Configuration & Colors ---
set -e

# Professional Palette
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color


# --- UI Helpers ---
log_success() { echo -e " ${GREEN}${BOLD}✓${NC} ${GREEN}$1${NC}"; }
log_error()   { echo -e " ${RED}${BOLD}✗${NC} ${RED}$1${NC}"; }
log_info()    { echo -e " ${BLUE}${BOLD}i${NC} ${BLUE}$1${NC}"; }
log_warn()    { echo -e " ${YELLOW}${BOLD}⚠${NC} ${YELLOW}$1${NC}"; }
header()      { echo -e "\n${PURPLE}${BOLD}=========== $1 ===========${NC}"; }


# --- Interactive Menu ---
show_menu() {
    clear
    echo -e "${CYAN}${BOLD}🍃 Green FinTech BaaS - Interactive CLI${NC}"
    echo -e "${YELLOW}Current Environment:${NC} $(poetry env info --path 2>/dev/null || echo 'None')"
    echo -e "-------------------------------------------------------------------------  "
    echo -e "${BOLD}Setup & Maintenance:${NC}"
    echo -e "  01) ${BLUE}[init]${NC}       Install all dependencies"
    echo -e "  02) ${BLUE}[lock]${NC}       Update lockfile & show tree"
    echo -e "  03) ${BLUE}[lint]${NC}       Format & Lint code"
    echo -e "${BOLD}Database Operations:${NC}"
    echo -e "  04) ${BLUE}[db-up]${NC}      Reset & Start Postgres"
    echo -e "  05) ${BLUE}[migrate]${NC}    Create & Apply migrations"
    echo -e "  06) ${BLUE}[db-stat]${NC}    Check DB health/stats"
    echo -e "  07) ${BLUE}[db-sql]${NC}     Run custom SQL"
    echo -e "${BOLD}Testing & Execution:${NC}"
    echo -e "  08) ${BLUE}[test]${NC}       Run Pytest (Standard)"
    echo -e "  09) ${BLUE}[cov]${NC}        Run Pytest (Coverage)"
    echo -e "  10) ${BLUE}[run]${NC}        Start FastAPI dev server"
    echo -e "${BOLD}Deployment:${NC}"
    echo -e "  11) ${BLUE}[build]${NC}      Package for PyPI"
    echo -e "  12) ${BLUE}[clean]${NC}      Remove cache & build artifacts"
    echo -e "   q) ${RED}[Quit]${NC}"
    echo -ne "\n${YELLOW}Select an option: ${NC}"
    read -r opt
    case $opt in
        1)  run_cmd "init" ;;
        2)  run_cmd "lock" ;;
        3)  run_cmd "lint" ;;
        4)  run_cmd "db-up" ;;
        5)  run_cmd "db-migrate" ;;
        6)  run_cmd "db-status" ;;
        7)  run_cmd "db-sql" ;;
        8)  run_cmd "test" ;;
        9)  run_cmd "test" "cov" ;;
        10) run_cmd "run" ;;
        11) run_cmd "build" ;;
        12) run_cmd "clean" ;;
        q)  exit 0 ;;
        *)  log_error "Invalid option"; sleep 1; show_menu ;;
    esac
}


# --- Command Logic ---
run_cmd() {
    case "$1" in
        "lock")
            header "UPDATING POETRY LOCKFILE"
            log_info "Resolving dependencies and updating lockfile..."

            poetry lock --regenerate
            log_info "Checking lockfile integrity..."

            poetry check --lock --strict
            log_info "Displaying dependency tree..."

            poetry show --tree
            log_success "Lockfile updated successfully."

            log_info "Re-installing dependencies in current environment..."
            poetry install
            ;;

        "init")
            header "INITIALIZING PROJECT DEPENDENCIES"
            log_info "Adding core dependencies..."
            poetry add fastapi httpx pydantic pydantic-settings "sqlalchemy[asyncio]" asyncpg "psycopg[binary]" alembic

            log_info "Adding development dependencies..."
            poetry add python-dotenv black isort ruff mypy pre-commit twine --group dev

            log_info "Adding testing dependencies..."
            poetry add pytest pytest-cov pytest-asyncio pytest-docker --group test

            log_info "Adding production dependencies..."
            poetry add uvicorn --group prod

            log_info "Adding documentation dependencies..."
            poetry add sphinx --group docs

            log_info "Exporting dependencies to requirements.txt..."
            poetry export -f requirements.txt --output requirements.txt --without-hashes

            log_info "Installing dependencies in current environment..."
            # --without test
            poetry install --with dev,test,prod,docs

            log_info "Setting up pre-commit hooks..."
            poetry run pre-commit install
            log_success "Dependencies added and environment initialized."
            ;;

        "lint")
            header "RUNNING STATIC ANALYSIS"
            log_info "Updating pre-commit hooks..."
            poetry run pre-commit autoupdate

            log_info "Showing unsafe fixes..."
            poetry run ruff check --unsafe-fixes src/ tests/ || true

            log_info "Running Ruff..."
            poetry run ruff check --fix src/ tests/ --show-diff-on-failure

            log_info "Ruff enforce check for F401 and F403 rules..."
            poetry run ruff check src/ tests/ --select F401,F403

            log_info "Running Black..."
            poetry run black src/ tests/

            log_info "Running Pre-commit hooks..."
            poetry run pre-commit run --all-files --verbose
            log_success "Linting complete."
            ;;

        "db-up")
            header "DATABASE MANAGEMENT"
            log_info "View existing containers..."
            docker ps -a

            log_info "Removing existing containers..."
            docker compose down --remove-orphans -v

            log_info "Starting PostgreSQL container..."
            docker compose up -d postgres

            log_info "Waiting for PG readiness..."
            sleep 2

            log_info "Starting postgres database..."
            ./scripts/db-helper.sh start
            log_success "PostgreSQL is active."
            ;;

        "db-migrate")
            header "ALEMBIC MIGRATIONS"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start

            log_info "Checking migration history..."
            # View migration script history from the latest revision to the given revision:
            # alembic history -r6df59d73aea3: --verbose
            alembic history --verbose | head -n 15

            log_info "Generating migration script..."
            read -p "Enter migration message: " msg
            alembic revision --autogenerate -m "$msg"

            log_info "Viewing generated migration script (SQL preview)..."
            alembic upgrade head --sql | tail -n 25

            log_info "Ready to apply..."
            # Revert to a previous version if needed:
            # alembic downgrade -1
            read -p "Apply migration to database? (y/n) " apply
            if [[ "$apply" == "y" ]]; then
                read -p "Enter migration tag (optional): " tag
                alembic upgrade head --tag "$tag"
                log_success "Migration applied successfully."
            else
                log_warn "Migration not applied. Remember to apply it before running the app!"
            fi
            ;;

        "db-status")
            header "DATABASE INSPECTION"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start

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
            log_success "Status check complete."
            ;;

        "db-sql")
            header "RUNNING CUSTOM SQL"
            log_info "Starting PostgreSQL Database..."
            ./scripts/db-helper.sh start

            # Tip: "\dt", "SELECT * FROM alembic_version;", "\di"
            log_info "Enter a SQL query (e.g., \dt or SELECT * FROM table;)"
            read -p "Enter SQL query: " query
            ./scripts/db-helper.sh sql "$query"
            log_success "Query executed."
            ;;

        "test")
            header "RUNNING TEST SUITE"
            # Tip: pytest -v --log-cli-level=DEBUG
            if [ "$2" == "cov" ]; then
                log_info "Running tests with coverage report..."
                poetry run pytest --cov=src --cov-report=term-missing
            else
                log_info "Running tests (standard mode)..."
                poetry run pytest -v -m "${2:-not slow}"
            fi
            ;;

        "build")
            header "PACKAGING FOR PYPI"
            log_info "Cleaning old build artifacts..."
            rm -rf dist/ build/ *.egg-info

            log_info "Building wheel and sdist..."
            poetry build
            log_success "Build artifacts created in dist/"
            ;;

        "publish-test")
            header "PUBLISHING TO TEST PYPI"
            # poetry config http-basic.pypi <user> <pass>
            # poetry config pypi-token.testpypi <token>
            log_info "Configuring repository..."
            poetry config repositories.testpypi https://test.pypi.org/legacy/

            log_info "Uploading package..."
            poetry run twine upload --repository testpypi dist/* --verbose
            ;;

        "clean")
            header "CLEANING PROJECT WORKSPACE"
            log_info "Removing Python byte-code and cache..."
            find . -type d -name "__pycache__" -exec rm -rf {} +
            find . -type f -name "*.py[co]" -delete

            log_info "Removing test and linting caches..."
            rm -rf .pytest_cache .coverage .mypy_cache .ruff_cache

            log_info "Removing build artifacts..."
            rm -rf dist/ build/ *.egg-info

            log_success "Workspace cleaned."
            ;;

        *)
            echo -e "${CYAN}${BOLD}Green FinTech BaaS - CLI Tools${NC}"
            echo -e "Usage: ./exec.sh [command]\n"
            echo -e "${BOLD}Available Commands:${NC}"
            echo -e "  ${BLUE}init${NC}          Install core/dev/test/prod/docs dependencies"
            echo -e "  ${BLUE}lock${NC}          Regenerate lockfile and show tree"
            echo -e "  ${BLUE}lint${NC}          Ruff fixes, Black, and Pre-commit"
            echo -e "  ${BLUE}db-up${NC}         Reset Docker and start Postgres"
            echo -e "  ${BLUE}db-migrate${NC}    Interactive Alembic revision & upgrade"
            echo -e "  ${BLUE}db-status${NC}     Full DB health & inspection"
            echo -e "  ${BLUE}db-sql${NC}        Execute manual SQL queries"
            echo -e "  ${BLUE}test${NC}          Run pytest (default: not slow)"
            echo -e "  ${BLUE}test cov${NC}      Run pytest with coverage"
            echo -e "  ${BLUE}build${NC}         Clean and build artifacts"
            echo -e "  ${BLUE}clean${NC}         Remove caches and temp files"
            echo -e "  ${BLUE}publish-test${NC}  Upload to TestPyPI"
            ;;
    esac
}


# --- Execution Entry ---
if [ -z "$1" ]; then
    show_menu
else
    run_cmd "$@"
fi
