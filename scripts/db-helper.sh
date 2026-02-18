#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

serious() {
    echo -e "${ORANGE}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

info() {
    echo -e "${BLUE}  $1${NC}"
}

data() {
    echo -e "${NC}  > $1${NC}"
}

# Load environment variables from .env
load_env() {
    if [ -f .env ]; then
        info "Loading configuration from .env file..."

        # Read .env line by line, ignoring comments and empty lines
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            if [[ ! "$line" =~ ^\s*# ]] && [[ -n "$line" ]]; then
                # Remove trailing comments and export
                clean_line=$(echo "$line" | sed 's/\s*#.*$//')
                export "$clean_line"
            fi
        done < .env

        # Display loaded configuration (hide password)
        success Loaded environment variables from .env:
        data "POSTGRES_USER: ${POSTGRES_USER}"
        data "POSTGRES_DB: ${POSTGRES_DB}"
        data "POSTGRES_PORT: ${POSTGRES_PORT}"
        data "POSTGRES_INITDB_ARGS: ${POSTGRES_INITDB_ARGS}"
        data "POSTGRES_PASSWORD: [HIDDEN]"
    else
        warn "No .env file found, using defaults"
        # Default values if no .env
        export POSTGRES_USER=postgres
        export POSTGRES_PASSWORD=postgres
        export POSTGRES_DB=green_fintech
        export POSTGRES_PORT=5432
        export POSTGRES_INITDB_ARGS="--auth=scram-sha-256"
    fi
}

# Set DATABASE_URL for applications (using asyncpg driver)
export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"

COMPOSE_CMD="docker compose"

# Create temporary .pgpass file in the container
setup_pgpass() {
    if ! docker ps --format '{{.Names}}' | grep -q "^green-fintech-db$"; then
        warn "PostgreSQL container not running, skipping .pgpass setup"
        return 1
    fi

    info "Setting up temporary .pgpass for secure authentication..."

    # Create .pgpass file with proper format: hostname:port:database:username:password
    local pgpass_content="localhost:${POSTGRES_PORT}:${POSTGRES_DB}:${POSTGRES_USER}:${POSTGRES_PASSWORD}"

    # Write to container and set secure permissions
    if docker exec green-fintech-db sh -c "echo '$pgpass_content' > /tmp/.pgpass && chmod 600 /tmp/.pgpass"; then
        success ".pgpass created successfully"

        # Verify the file exists and has correct permissions
        docker exec green-fintech-db sh -c "ls -la /tmp/.pgpass" > /dev/null 2>&1
        return 0
    else
        error "Failed to create .pgpass"
        return 1
    fi
}

# Clean up .pgpass file
cleanup_pgpass() {
    if docker ps --format '{{.Names}}' | grep -q "^green-fintech-db$"; then
        if docker exec green-fintech-db sh -c "test -f /tmp/.pgpass" 2>/dev/null; then
            warn "Cleaning up temporary .pgpass file..."
            docker exec green-fintech-db rm /tmp/.pgpass
            success ".pgpass removed"
        fi
    fi
}

# Set trap to ensure cleanup on script exit
trap cleanup_pgpass EXIT

check_postgres() {
    if docker ps --format '{{.Names}}' | grep -q "^green-fintech-db$"; then
        if docker exec green-fintech-db pg_isready -U ${POSTGRES_USER} >/dev/null 2>&1; then
            success "PostgreSQL is running and accepting connections"

            # Show authentication method (for verification)
            AUTH_METHOD=$(docker exec green-fintech-db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT auth_method FROM pg_hba_file_rules WHERE auth_method IS NOT NULL LIMIT 1;" 2>/dev/null | xargs)
            if [ -n "$AUTH_METHOD" ]; then
                warn "  Authentication: ${AUTH_METHOD:-scram-sha-256}"
            fi
            return 0
        else
            warn "PostgreSQL container is running but not yet accepting connections"
            return 1
        fi
    else
        error "PostgreSQL container is not running"
        return 1
    fi
}

start() {
    warn "Starting PostgreSQL with SCRAM-SHA-256 authentication..."

    # Export environment variables for docker-compose
    export POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB POSTGRES_PORT POSTGRES_INITDB_ARGS

    $COMPOSE_CMD up -d postgres

    # Wait for PostgreSQL to be ready
    echo
    warn "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec green-fintech-db pg_isready -U ${POSTGRES_USER} >/dev/null 2>&1; then
            success "PostgreSQL is ready with SCRAM-SHA-256 authentication"

            # Verify authentication method
            sleep 2  # Give PostgreSQL a moment to fully initialize
            AUTH_CHECK=$(docker exec green-fintech-db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT 'Authentication: ' || auth_method FROM pg_hba_file_rules WHERE auth_method IS NOT NULL LIMIT 1;" 2>/dev/null || echo "")
            if [ -n "$AUTH_CHECK" ]; then
                success "$AUTH_CHECK"
            fi
            return 0
        fi
        echo -n "."
        sleep 1
    done
    error "Timed out waiting for PostgreSQL"
    return 1
}

stop() {
    warn "Stopping PostgreSQL..."
    $COMPOSE_CMD stop postgres
    success "PostgreSQL stopped"
}

reset() {
    serious "WARNING: This will delete ALL data!"
    warn "Database: ${POSTGRES_DB}"
    warn "User: ${POSTGRES_USER}"
    read -p " Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        warn "Stopping and removing volumes..."
        $COMPOSE_CMD down -v
        echo
        warn "Starting fresh with SCRAM-SHA-256 authentication..."
        echo
        start
        success "Database reset complete with secure authentication"
    fi
}

psql() {
    # Connect with explicit password (will prompt if not set)
    if [ -n "$POSTGRES_PASSWORD" ]; then
        export PGPASSWORD=$POSTGRES_PASSWORD
        docker exec -e PGPASSWORD -it green-fintech-db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
    else
        docker exec -it green-fintech-db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
    fi
}

logs() {
    docker logs -f green-fintech-db
}

backup() {
    mkdir -p backups
    local backup_file="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    warn "Creating backup: $backup_file"

    if [ -n "$POSTGRES_PASSWORD" ]; then
        export PGPASSWORD=$POSTGRES_PASSWORD
        docker exec -e PGPASSWORD green-fintech-db pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "$backup_file"
    else
        docker exec green-fintech-db pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "$backup_file"
    fi

    success "Backup created: $backup_file ($(du -h "$backup_file" | cut -f1))"
}

restore() {
    local backup_file=$1
    if [ ! -f "$backup_file" ]; then
        error "Error: Backup file not found: $backup_file"
        exit 1
    fi

    warn "Restoring from: $backup_file"
    serious "WARNING: This will overwrite current data!"
    read -p "Continue? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -n "$POSTGRES_PASSWORD" ]; then
            export PGPASSWORD=$POSTGRES_PASSWORD
            cat "$backup_file" | docker exec -e PGPASSWORD -i green-fintech-db psql -U ${POSTGRES_USER} ${POSTGRES_DB}
        else
            cat "$backup_file" | docker exec -i green-fintech-db psql -U ${POSTGRES_USER} ${POSTGRES_DB}
        fi
        success "Restore complete"
    fi
}

show_config() {
    echo
    info "Current PostgreSQL Configuration:"
    data "User: ${POSTGRES_USER}"
    data "Database: ${POSTGRES_DB}"
    data "Port: ${POSTGRES_PORT}"
    data "Init Args: ${POSTGRES_INITDB_ARGS}"
    data "DATABASE_URL: ${DATABASE_URL/postgres:$POSTGRES_PASSWORD@/postgres:[HIDDEN]@}"

    if check_postgres >/dev/null 2>&1; then
        echo
        info "Runtime Configuration:"

        # Try multiple methods to query settings
        if [ -n "$POSTGRES_PASSWORD" ]; then
            docker exec -e PGPASSFILE=/tmp/.pgpass green-fintech-db \
                psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
                -c "SELECT name, setting, unit FROM pg_settings WHERE name IN ('password_encryption', 'ssl', 'log_connections', 'max_connections') ORDER BY name;" 2>/dev/null
            local result=$?

            if [ $result -eq 0 ]; then
                return
            fi
        fi

        warn "Unable to query runtime settings (authentication required)"
        info "Run './scripts/db-helper.sh psql' to connect interactively"
    fi
}

# Run a SQL command and return results
run_sql() {
    local query="$1"
    if [ -z "$query" ]; then
        error "Error: No SQL query provided"
        return 1
    fi

    # Use PGPASSWORD environment variable
    docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" green-fintech-db \
        psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        -t -c "$query" 2>/dev/null || {
        error "Error running SQL command"
        return 1
    }
}

# Show active connections
active_connections() {
    echo
    info "Active Database Connections:"
    run_sql "SELECT
        pid,
        usename,
        application_name,
        client_addr,
        state,
        query_start
    FROM pg_stat_activity
    WHERE state = 'active'
    ORDER BY query_start DESC;"
}

# Show database statistics
db_stats() {
    echo
    info "Database Statistics:"
    run_sql "SELECT
        datname as database_name,
        numbackends as connections,
        xact_commit as transactions,
        blks_read as blocks_read,
        blks_hit as cache_hits,
        ROUND(blks_hit::numeric / (blks_read + blks_hit) * 100, 2) as cache_hit_ratio
    FROM pg_stat_database
    WHERE datname = '${POSTGRES_DB}';"
}

# Show table sizes
table_sizes() {
    echo
    info "Table Sizes:"
    run_sql "SELECT
        relname as table_name,
        pg_size_pretty(pg_total_relation_size(relid)) as total_size,
        pg_size_pretty(pg_relation_size(relid)) as data_size,
        pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size,
        n_live_tup as rows
    FROM pg_stat_user_tables
    ORDER BY pg_total_relation_size(relid) DESC;"
}


# Main script execution
main() {
    # Load environment variables first
    load_env

    # Check if container is running and setup .pgpass
    if docker ps --format '{{.Names}}' | grep -q "^green-fintech-db$"; then
        setup_pgpass
    fi

    # Execute command
    case "${1:-}" in
        start) start ;;
        stop) stop ;;
        restart) stop; sleep 2; start ;;
        status) check_postgres ;;
        reset) reset ;;
        psql) psql ;;
        logs) logs ;;
        backup) backup ;;
        restore) restore "$2" ;;
        config) show_config ;;
        connections) active_connections ;;
        stats) db_stats ;;
        tables) table_sizes ;;
        sql) run_sql "$2" ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|reset|psql|logs|backup|restore|config|connections|stats|tables|sql}"
            echo
            echo "Commands:"
            info "start        - Start PostgreSQL with SCRAM-SHA-256 auth"
            info "stop         - Stop PostgreSQL container"
            info "restart      - Restart PostgreSQL container"
            info "status       - Check if PostgreSQL is running"
            info "reset        - WARNING: Delete all data and start fresh"
            info "psql         - Connect to PostgreSQL with psql"
            info "logs         - Show PostgreSQL logs"
            info "backup       - Create a database backup"
            info "restore      - Restore from a backup file"
            info "config       - Show current configuration"
            info "connections  - Show active database connections"
            info "stats        - Show database statistics"
            info "tables       - Show table sizes"
            info "sql 'query'  - Run a SQL query"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
