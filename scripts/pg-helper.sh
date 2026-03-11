#!/bin/bash
# scripts/pg-helper.sh

set -e

# --- Configuration ---
# Import the common library relative to this script's location
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

PG_CONTAINER="green-fintech-db"

show_env() {
    echo
    log_info "Current Postgres Configuration:"
    log_data "Container: ${PG_CONTAINER}"
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
    _exec_db -it "${PG_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" "$@"
}

_psql_query() {
    _exec_db -it "${PG_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "$1"
}

_is_ready() {
    docker exec "${PG_CONTAINER}" pg_isready -U "${POSTGRES_USER}" >/dev/null 2>&1
}

# --- Service Management ---
check_postgres() {
    if docker ps --format '{{.Names}}' | grep -q "^${PG_CONTAINER}$"; then
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
    _compose_up "postgres" && log_success "Postgres service up"

    log_warn "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if _is_ready; then
            echo
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
    _compose_stop "postgres"
    log_success "PostgreSQL stopped"
}

wipe() {
    log_serious "WARNING: This will delete ALL data!"
    if ask_yes_no "Are you sure?"; then
        _compose_down "postgres"
        start
        log_success "Database wipe complete"
    fi
}

# --- Alembic Migrations ---
mig_new() {
    header "NEW MIGRATION"
    assert_cmd "PostgreSQL is active." "Database unavailable" start

    log_info "Generating migration script..."
    read -p "Enter migration message: " msg
    if [ -n "$msg" ]; then
        uv run alembic revision --autogenerate -m "$msg" && log_success "Migration created in ./alembic/versions"
    else
        log_error "Migration message cannot be empty."
        exit 1
    fi
    mig_up
}

mig_up() {
    header "UPGRADING SCHEMA"
    log_info "Readying to apply..."
    read -p "Enter migration tag (optional): " tag
    if [ -n "$tag" ]; then
        assert_cmd "Migration applied successfully." "Migrations failed" uv run alembic upgrade head --tag "$tag"
    else
        assert_cmd "Migration applied successfully." "Migrations failed" uv run alembic upgrade head
    fi
}

mig_stat() {
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
}

seed() {
    header "POSTGRES DB INITIALISATION"
    log_info "Starting PostgreSQL Database..."
    assert_cmd "PostgreSQL is active." "Database failed to start" start

    mig_new

    log_warn "Waiting for PostgreSQL to commit DDL changes..."
    sleep 2

    log_info "Seeding data..."
    assert_cmd "Seeds planted" "Database seeding failed" uv run python -m scripts.seed_db
    log_success "Postgres db fully initialised."
}

# --- Database Backup & Restore ---
backup() {
    mkdir -p backups
    local backup_file="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    log_warn "Creating backup: $backup_file..."
    _exec_db "${PG_CONTAINER}" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "$backup_file"
    log_success "Backup created: $backup_file ($(du -h "$backup_file" | cut -f1))"
}

restore() {
    local backup_file=$1
    if [ ! -f "$backup_file" ]; then
        log_error "Error: Backup file not found: $backup_file"
        exit 1
    fi
    log_serious "WARNING: This will overwrite current data!"
    if ask_yes_no "Continue?"; then
        cat "$backup_file" | _exec_db -i "${PG_CONTAINER}" psql -U "${POSTGRES_USER}" "${POSTGRES_DB}"
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
    if [ -n "$query" ]; then
        _psql -t -c "$query" 2>/dev/null || log_error "Error running SQL command"
        return
    fi

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
    if _exec_db -it "${PG_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT 1" >/dev/null 2>&1; then
        log_success "Success"
    else
        log_error "Failed"
    fi

    echo -n "  Method 2 (URI string): "
    if _exec_db "${PG_CONTAINER}" psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}" -c "SELECT 1" >/dev/null 2>&1; then
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

dump() {
    log_info "1. Registered Companies:"
    _psql_query "SELECT id, companies_house_id, name, location FROM companies LIMIT 10;"
    echo
    log_info "2. Primary Environmental Metrics:"
    _psql_query "SELECT id, company_id, reporting_year, carbon_emissions_tco2e FROM environmental_metrics LIMIT 10;"
    echo
    log_info "3. Generated Loan Simulations:"
    _psql_query "SELECT id, company_id, loan_amount, applied_rate, esg_score FROM loan_simulations LIMIT 10;"
}

# --- Execution Entry ---
main() {
    load_env

    case "${1:-}" in
        start) start ;;
        stop) stop ;;
        status) check_postgres ;;
        wipe) wipe ;;
        psql) _psql ;;
        logs) docker logs -f "${PG_CONTAINER}" ;;

        mig-new) mig_new ;;
        mig-up) mig_up ;;
        mig-stat) mig_stat ;;
        seed) seed ;;

        backup) backup ;;
        restore) restore "$2" ;;

        config) show_config ;;
        connections) active_connections ;;
        stats) db_stats ;;
        tables) table_sizes ;;
        sql) run_sql "$2" ;;
        test-access) test_access ;;
        inspect) inspect_db ;;
        dump) dump ;;
        *)
            echo "Usage: $0 {start|stop|status|wipe|psql|logs|mig-new|mig-up|mig-stat|seed|backup|restore|config|connections|stats|tables|sql|test-access|inspect|dump}"
            exit 1
            ;;
    esac
}

main "$@"
