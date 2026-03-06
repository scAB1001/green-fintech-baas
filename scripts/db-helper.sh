#!/bin/bash
set -e

# --- Configuration & Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

DB_CONTAINER="green-fintech-db"
COMPOSE_CMD="docker compose"

# --- UI Helpers ---
log_warn()      { echo -e " ${YELLOW}${BOLD}⚠${YELLOW} $1${NC}"; }
log_serious()   { echo -e " ${ORANGE}${BOLD}⚠${ORANGE} $1${NC}"; }
log_error()     { echo -e " ${RED}${BOLD}✗${RED} $1${NC}"; }
log_success()   { echo -e " ${GREEN}${BOLD}✓${NC} ${GREEN}$1${NC}"; }
log_data()      { echo -e " ${NC}${BOLD}  >${NC} $1${NC}"; }
log_info()      { echo -e " ${BLUE}${BOLD}i${BLUE} $1${NC}"; }

# --- Environment Setup ---
load_env() {
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
        export POSTGRES_USER=postgres
        export POSTGRES_PASSWORD=postgres
        export POSTGRES_DB=green_fintech
        export POSTGRES_PORT=5432
        export POSTGRES_INITDB_ARGS="--auth=scram-sha-256"
    fi

    # Exported globally for external tools if needed
    export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
}

show_env() {
    echo
    log_info "Current Environment Configuration:"
    log_data "User: ${POSTGRES_USER}"
    log_data "Database: ${POSTGRES_DB}"
    log_data "Port: ${POSTGRES_PORT}"
    log_data "Init Args: ${POSTGRES_INITDB_ARGS}"
}

# --- Core command wrappers ---
_exec_db() {
    docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "$@"
}

_psql() {
    _exec_db "${DB_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" "$@"
}

_is_ready() {
    docker exec "${DB_CONTAINER}" pg_isready -U "${POSTGRES_USER}" >/dev/null 2>&1
}

# --- Service Management ---
check_postgres() {
    if docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
        if _is_ready; then
            log_success "PostgreSQL is running and accepting connections"
            return 0
        else
            log_warn "PostgreSQL container is running but not yet accepting connections"
            return 1
        fi
    else
        log_error "PostgreSQL container is not running"
        return 1
    fi
}

start() {
    log_warn "Starting PostgreSQL with SCRAM-SHA-256 authentication..."
    $COMPOSE_CMD up -d postgres && log_success "Postgres service up"

    log_warn "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if _is_ready; then
            log_success "PostgreSQL is ready"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    log_error "Timed out waiting for PostgreSQL"
    return 1
}

stop() {
    log_warn "Stopping PostgreSQL..."
    $COMPOSE_CMD stop postgres
    log_success "PostgreSQL stopped"
}

reset() {
    log_serious "WARNING: This will delete ALL data!"
    read -p " Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $COMPOSE_CMD down -v
        start
        log_success "Database reset complete"
    fi
}

# --- Database Operations ---
psql() {
    _exec_db -it "${DB_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
}

logs() {
    docker logs -f "${DB_CONTAINER}"
}

backup() {
    mkdir -p backups
    local backup_file="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    log_warn "Creating backup: $backup_file..."
    _exec_db "${DB_CONTAINER}" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "$backup_file"
    log_success "Backup created: $backup_file ($(du -h "$backup_file" | cut -f1))"
}

restore() {
    local backup_file=$1
    if [ ! -f "$backup_file" ]; then
        log_error "Error: Backup file not found: $backup_file"
        exit 1
    fi
    log_serious "WARNING: This will overwrite current data! Continue? (y/N)"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat "$backup_file" | _exec_db -i "${DB_CONTAINER}" psql -U "${POSTGRES_USER}" "${POSTGRES_DB}"
        log_success "Restore complete"
    fi
}

# --- Diagnostics & Queries ---
show_config() {
    show_env
    if check_postgres >/dev/null 2>&1; then
        echo
        log_info "Runtime Configuration:"
        _psql -c "SELECT name, setting, unit FROM pg_settings WHERE name IN ('password_encryption', 'ssl', 'log_connections', 'max_connections') ORDER BY name;" 2>/dev/null
    fi
}

run_sql() {
    local query="$1"

    # Single execution
    if [ -n "$query" ]; then
        _psql -t -c "$query" 2>/dev/null || log_error "Error running SQL command"
        return
    fi

    # Interactive mode
    log_info "Interactive SQL Mode. Type 'q' or 'quit' to exit."
    while true; do
        read -p "SQL> " query
        if [[ "$query" == "q" || "$query" == "quit" ]]; then
            log_success "Exiting SQL mode."
            break
        fi
        if [ -n "$query" ]; then
            _psql -c "$query" || log_error "Error executing query."
        fi
    done
}

active_connections() {
    log_info "Active Database Connections:"
    _psql -c "SELECT pid, usename, application_name, client_addr, state, query_start FROM pg_stat_activity WHERE state = 'active' ORDER BY query_start DESC;"
}

db_stats() {
    log_info "Database Statistics:"
    _psql -c "SELECT datname as database_name, numbackends as connections, xact_commit as transactions, blks_read as blocks_read, blks_hit as cache_hits, ROUND(blks_hit::numeric / (blks_read + blks_hit) * 100, 2) as cache_hit_ratio FROM pg_stat_database WHERE datname = '${POSTGRES_DB}';"
}

table_sizes() {
    log_info "Table Sizes:"
    _psql -c "SELECT relname as table_name, pg_size_pretty(pg_total_relation_size(relid)) as total_size, pg_size_pretty(pg_relation_size(relid)) as data_size, pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size, n_live_tup as rows FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC;"
}

test_access() {
    log_info "Testing PostgreSQL access methods:"

    echo -n "  Method 1 (PGPASSWORD Env Var): "
    if _psql -c "SELECT 1" >/dev/null 2>&1; then
        log_success "Success"
    else
        log_error "Failed"
    fi

    echo -n "  Method 2 (URI string): "
    if _exec_db "${DB_CONTAINER}" psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}" -c "SELECT 1" >/dev/null 2>&1; then
        log_success "Success"
    else
        log_error "Failed"
    fi
}

inspect_db() {
    test_access
    show_config
    active_connections
    db_stats
    table_sizes
}

# --- Execution Entry ---
main() {
    load_env

    case "${1:-}" in
        start) start ;;
        stop) stop ;;
        restart) stop; sleep 2; start ;;
        st|status) check_postgres ;;
        reset) reset ;;
        psql) psql ;;
        logs) logs ;;
        backup) backup ;;
        restore) restore "$2" ;;
        cn|config) show_config ;;
        connections) active_connections ;;
        stats) db_stats ;;
        tables) table_sizes ;;
        sql) run_sql "$2" ;;
        test-access) test_access ;;
        inspect) inspect_db ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|reset|psql|logs|backup|restore|config|connections|stats|tables|sql|test-access|inspect}"
            echo
            echo "Commands:"
            log_info "start        - Start PostgreSQL with SCRAM-SHA-256 auth"
            log_info "stop         - Stop PostgreSQL container"
            log_info "restart      - Restart PostgreSQL container"
            log_info "status       - Check if PostgreSQL is running"
            log_info "reset        - WARNING: Delete all data and start fresh"
            log_info "psql         - Connect to PostgreSQL with psql"
            log_info "logs         - Show PostgreSQL logs"
            log_info "backup       - Create a database backup"
            log_info "restore      - Restore from a backup file"
            log_info "config       - Show current configuration"
            log_info "connections  - Show active database connections"
            log_info "stats        - Show database statistics"
            log_info "tables       - Show table sizes"
            log_info "sql 'query'  - Run a SQL query"
            log_info "test-access  - Test all access methods"
            log_info "inspect      - Inspect db"
            echo
            exit 1
            ;;
    esac
}

main "$@"
