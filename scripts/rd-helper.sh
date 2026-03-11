#!/bin/bash
# scripts/rd-helper.sh

set -e

# --- Configuration ---
# Import the common library relative to this script's location
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

RD_CONTAINER="green-fintech-cache"

show_env() {
    echo
    log_info "Current Cache Configuration:"
    log_data "Container: ${RD_CONTAINER}"
    log_data "Port: ${REDIS_PORT}"
}

# --- Core command wrappers ---
_redis() {
    docker exec -e REDISCLI_AUTH="${REDIS_PASSWORD}" "${RD_CONTAINER}" redis-cli "$@"
}

_redis_it() {
    docker exec -it -e REDISCLI_AUTH="${REDIS_PASSWORD}" "${RD_CONTAINER}" redis-cli "$@"
}

_redis_ping() {
    _redis ping | grep -q "PONG"
}

_api_post() {
    curl -s -o /dev/null -w "%{http_code}" -X 'POST' "${ROOT_URL}$1" \
        -H 'Content-Type: application/json' -H 'accept: application/json' -d "$2"
}

_api_delete() {
    curl -s -o /dev/null -w "%{http_code}" -X 'DELETE' "${ROOT_URL}$1" \
        -H 'accept: application/json'
}

# --- Service Management ---
check_redis() {
    if docker ps --format '{{.Names}}' | grep -q "^${RD_CONTAINER}$"; then
        if _redis_ping; then
            log_success "Redis is running and responding to PING"
            return 0
        else
            log_warn "Redis container is running but not responding"
            return 1
        fi
    else
        log_error "Redis container is not running"
        return 1
    fi
}

start() {
    log_warn "Starting Redis Service..."
    _compose_up "redis" && log_success "Redis container up"

    log_warn "Waiting for Redis to be ready..."
    for i in {1..10}; do
        if _redis_ping; then
            log_success "Redis is ready"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    log_error "Timed out waiting for Redis"
    return 1
}

stop() {
    log_warn "Stopping Redis..."
    _compose_stop "redis"
    log_success "Redis stopped"
}

reset() {
    log_serious "WARNING: This will destroy the Redis container!"
    if ask_yes_no "Are you sure?"; then
        _compose_down "redis"
        start
        log_success "Redis reset complete"
    fi
}

# --- Cache Operations & Toolkit ---
flush() {
    log_info "Flushing Redis Cache..."
    if check_redis >/dev/null 2>&1; then
        assert_cmd "Redis cache cleared (FLUSHALL)" "Failed to clear Redis" _redis FLUSHALL
    fi
}

cli() {
    log_info "Entering Interactive Redis CLI. Type 'exit' to leave."
    _redis_it
}

monitor() {
    log_info "Entering Real-time Monitor Mode. Press Ctrl+C to stop."
    _redis_it monitor
}

latency() {
    log_info "Running Latency Test. Press Ctrl+C to stop."
    _redis_it --latency
}

memory() {
    header "REDIS MEMORY PROFILING"
    if check_redis >/dev/null 2>&1; then
        log_info "Memory Usage Metrics:"
        _redis info memory | grep -E "used_memory_human|used_memory_peak_human|maxmemory_human|memory_fragmentation_ratio" | sed 's/^/  > /'

        echo
        log_info "Cache Key Distribution:"
        local keyspace=$(_redis info keyspace | grep "^db0")
        if [ -n "$keyspace" ]; then
            log_data "$keyspace"
        else
            log_data "No keys found in db0."
        fi
    fi
}

status() {
    header "REDIS STATUS"
    show_env
    if check_redis >/dev/null 2>&1; then
        log_info "Number of existing keys..."
        local key_count=$(_redis DBSIZE | tr -d '\r')
        log_data "DBSIZE: ${key_count}"

        if [ "$key_count" -gt 0 ]; then
            log_info "Current Keys:"
            _redis KEYS "*" | sed 's/^/  > /'
        fi
    fi
}

logs() {
    docker logs -f "${RD_CONTAINER}"
}

# --- End-to-End Diagnostics ---
diagnostics() {
    header "CACHING & INVALIDATION DIAGNOSTICS"

    if ! curl -s "${ROOT_URL}/health" >/dev/null; then
        log_error "API is not running at ${ROOT_URL}. Start it first."
        exit 1
    fi

    log_info "1. Timing CSV Export (Cache Miss - DB Generation)..."
    time curl -s -o /dev/null -X 'GET' "${HOST_URL}companies/export/csv"

    echo
    log_info "2. Timing CSV Export (Cache Hit - Should be INSTANT)..."
    time curl -s -o /dev/null -X 'GET' "${HOST_URL}companies/export/csv"

    echo
    log_info "3. Timing PDF Generation (Cache Miss - CPU Generation)..."
    time curl -s -o /dev/null -X 'GET' "${HOST_URL}companies/1/simulate-loan/1/pdf"

    echo
    log_info "4. Timing PDF Generation (Cache Hit - Base64 Decode)..."
    time curl -s -o /dev/null -X 'GET' "${HOST_URL}companies/1/simulate-loan/1/pdf"

    echo
    log_info "5. Current Redis Keys (Should contain CSV and PDF):"
    _redis KEYS "*" | sed 's/^/  > /'

    log_info "6. Ingesting Barclays (01026167) to trigger POST invalidation..."
    assert_cmd "Ingestion complete." "Ingestion failed" _api_post "/api/v1/companies/" '{"company_number": "01026167"}'

    log_info "7. Checking Redis Keys (The 'companies:csv' key should be purged):"
    _redis KEYS "*" | sed 's/^/  > /'

    log_info "8a. Re-caching the CSV file..."
    curl -s -o /dev/null -X 'GET' "${HOST_URL}companies/export/csv"

    log_info "8b. Fetching metrics to cache them..."
    curl -s -o /dev/null -X 'GET' "${HOST_URL}companies/1/metrics"

    log_info "8c. Adding 2025 metrics to trigger POST invalidation..."
    _api_post "/api/v1/companies/1/metrics" '{"reporting_year": 2025, "energy_consumption_mwh": 4000.0, "carbon_emissions_tco2e": 200.0}'

    log_info "9. Triggering DELETE invalidation (Removing Company ID 2)..."
    assert_cmd "Deletion complete." "Deletion failed" _api_delete "/api/v1/companies/2"

    log_info "10. Final Redis Keys (The 'companies:csv' key should be purged again):"
    _redis KEYS "*" | sed 's/^/  > /'

    log_success "Cache behavior diagnostics complete."
}

# --- Execution Entry ---
main() {
    load_env

    case "${1:-}" in
        start) start ;;
        stop) stop ;;
        status) status ;;
        reset) reset ;;
        flush) flush ;;
        cli) cli ;;
        monitor) monitor ;;
        latency) latency ;;
        memory) memory ;;
        logs) logs ;;
        diagnostics) diagnostics ;;
        *)
            echo "Usage: $0 {start|stop|status|reset|flush|cli|monitor|latency|memory|logs|diagnostics}"
            echo
            echo "Commands:"
            log_info "start        - Start Redis container"
            log_info "stop         - Stop Redis container"
            log_info "status       - Ping Redis and list current keys"
            log_info "reset        - Destroy and recreate Redis container"
            log_info "flush        - Clear all data in cache (FLUSHALL)"
            log_info "cli          - Enter interactive Redis CLI"
            log_info "monitor      - Real-time stream of Redis commands"
            log_info "latency      - Run continuous latency sampling"
            log_info "memory       - Profile memory usage and fragmentation"
            log_info "logs         - Tail container logs"
            log_info "diagnostics  - Run E2E cache invalidation and timing tests"
            echo
            exit 1
            ;;
    esac
}

main "$@"
