#!/bin/bash
# exec.sh

set -e

# --- Import Common Library ---
# This safely loads colors, UI helpers, load_env, and docker wrappers
source "$(dirname "${BASH_SOURCE[0]}")/scripts/common.sh"

opt()           { echo -ne "${NC}${BOLD}[${BLUE}$1${NC}${BOLD}]${NC}"; }


# --- Command wrappers for other files ---
_pg_exec() {
    ./scripts/pg-helper.sh "$@"
}

_rd_exec() {
    ./scripts/rd-helper.sh "$@"
}

_api_exec() {
    ./scripts/api-helper.sh "$@"
}


# --- Interactive Menu ---
show_menu() {
    clear

    local uv_cache_info="N/A"
    if command -v uv >/dev/null 2>&1; then
        uv_cache_info=$(uv cache size --preview-features cache-size 2>/dev/null || echo "Unknown")
    fi

    echo -e "${CYAN}${BOLD}🍃 Green FinTech BaaS - Orchestrator${NC}      ${YELLOW}UV Cache:${NC} $uv_cache_info"
    echo -e "-------------------------------------------------------------------------------------"

    echo -e "${BOLD}🛠️  Core Setup & Maintenance${NC}"
    echo -e "  01) $(opt "init")        Full Install (UV)        02) $(opt "lint")        Ruff/Black/Mypy"
    echo -e "  03) $(opt "clean")       Deep Workspace Purge     04) $(opt "kill")        Kill Ports 8000 & 8080"

    echo -e "\n${BOLD}🐘 Postgres Database (Local/Docker)${NC}"
    echo -e "  05) $(opt "db-up")       Start PG Container       06) $(opt "db-seed")     Seed PG Database"
    echo -e "  07) $(opt "db-stat")     Health & Stats           08) $(opt "db-wipe")     Nuke PG Volume & Reset"
    echo -e "  08b) $(opt "db-dump")    Dump Table Data"

    echo -e "\n${BOLD}🚀 Redis Cache Service${NC}"
    echo -e "  09) $(opt "rd-up")       Start Redis Container    10) $(opt "rd-stat")     Ping & Key Check"

    echo -e "\n${BOLD}⚗️  Alembic Migrations${NC}"
    echo -e "  11) $(opt "mig-new")     Create Autogen Rev       12) $(opt "mig-up")      Preview & Apply"
    echo -e "  13) $(opt "mig-stat")    History & Rollback"

    echo -e "\n${BOLD}🌐 FastAPI Service${NC}"
    echo -e "  14) $(opt "api-up")      Start FastAPI Container  15) $(opt "api-stat")    Health/Docs/Endpoint"
    echo -e "  16) $(opt "run")         Local Uvicorn Server"

    echo -e "\n${BOLD}🧪 Testing, Building and Publishing${NC}"
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

        5|db-up)     header "POSTGRES"; _pg_exec "start" ;;
        6|db-seed)   header "SEEDING";  _pg_exec "seed" ;;
        7|db-stat)   header "DB STATS"; _pg_exec "inspect" ;;
        8|db-wipe)   header "DB WIPE";  _pg_exec "wipe" ;;
        8b|db-dump)  header "DB DUMP";  _pg_exec "dump" ;;

        9|rd-up)     header "REDIS";    _rd_exec "start" ;;
        10|rd-stat)  header "REDIS STAT"; _rd_exec "status" ;;

        11|mig-new)  _pg_exec "mig"-new ;;
        12|mig-up)   _pg_exec "mig"-up ;;
        13|mig-stat) _pg_exec "mig"-stat ;;

        14|api-up)   header "FASTAPI";  _api_exec "start" ;;
        15|api-stat) header "API E2E";  _api_exec "status" ;;
        16|run)      header "UVICORN";  _api_exec "run" ;;

        17|test)     run_script "test" ;;
        18|e2e)      run_script "e2e" ;;
        19|stack)    run_script "docker-stack" ;;
        20|down) run_script "docker-down" ;;

        q|quit|exit) log_success "Exiting..."; exit 0 ;;
        *)  log_error "Invalid option"; sleep 1; show_menu ;;
    esac
}

# --- Command Logic (Global/Project Commands) ---
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
            if ask_yes_no "Would you like to view the dependency tree?"; then uv tree --all-groups; fi
            log_info "Exporting dependencies to requirements.txt..."
            assert_cmd "Lockfiles updated successfully." "Export failed" uv export --format requirements.txt --output-file requirements.txt
            ;;

        "lint")
            header "LINTING & FORMATTING"
            log_info "Updating pre-commit hooks..."
            assert_cmd "Pre-commit hooks updated" "Pre-commit autoupdate failed" uv run pre-commit autoupdate
            log_info "Running Ruff Check..."
            assert_cmd "Ruff finished" "Ruff found issues" uv run ruff check --fix .
            log_info "Running Ruff Format (Black equivalent)..."
            assert_cmd "Format finished" "Formatting failed" uv run ruff format .
            log_info "Running Mypy..."
            assert_cmd "Mypy checks passed" "Mypy found type errors" uv run mypy ./src/app/ --strict
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
                fi

                _docker_prune
                _rd_exec "flush" 2>/dev/null || true
                log_success "Workspace cleaned."
            fi
            ;;

        "kill"|"kill-ports")
            _api_exec "kill"
            ;;

        "test")
            _api_exec "kill" || true
            log_info "Wiping test containers and volumes..."
            _compose_wipe

            header "RUNNING TEST SUITE"
            if ask_yes_no "Run with coverage report?"; then
                log_info "Running tests with coverage report..."
                assert_cmd "Coverage report generated in htmlcov/index.html" "Tests failed." uv run pytest --cov=src --cov-report=html
                log_info "Opening coverage report in browser..."
                xdg-open htmlcov/index.html 2>/dev/null || true
            else
                log_info "Running tests (standard mode)..."
                assert_cmd "Tests passed" "Tests failed." uv run pytest -v
            fi
            ;;

        "e2e")
            header "END-TO-END ARCHITECTURE TEST"
            log_info "1. Testing Database Health..."
            _pg_exec "inspect"
            log_info "2. Testing Redis Cache..."
            _rd_exec "diagnostics"
            log_info "3. Testing FastAPI & File Generation..."
            _api_exec "status"
            header "END-TO-END TEST COMPLETE"
            ;;

         "stack"|"docker-stack")
            _api_exec "kill" || true
            header "DOCKER COMPOSE STACK"
            log_info "Clearing space..."
            _compose_wipe

            if ask_yes_no "Would you like to build the containers from scratch?"; then
                assert_cmd "Stack built from scratch" "Stack failed to start." _compose_build_up
            else
                assert_cmd "Stack up and running" "Stack failed to start." _compose_up
            fi

            sleep 3
            if ask_yes_no "Would you like to reinitialise/seed the database?"; then
                _pg_exec "seed"
            fi
            log_success "Stack running in background"
            ;;

        "down"|"docker-down")
            header "DOCKER COMPOSE DOWN"
            _docker_down_all
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
