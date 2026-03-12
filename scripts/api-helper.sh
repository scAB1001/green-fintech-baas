#!/bin/bash
# scripts/api-helper.sh

set -e

# --- Configuration ---
# Import the common library relative to this script's location
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

API_CONTAINER="green-fintech-api"

show_env() {
    echo
    log_info "Current API Configuration:"
    log_data "Container: ${API_CONTAINER}"
    log_data "Root URL (${API_PORT}): ${ROOT_URL}"
    log_data "Host URL (V1): ${HOST_URL}"
    log_data "Output Dir: ${OUT_DIR}"
}

# --- API Curl Wrappers ---
# Note: Since $1 might be "/companies", we strip leading slashes
# from the argument so the url resolves cleanly to "http.../api/v1/companies"
# Usage: _api_get "/endpoint" | "endpoint"
_api_get() {
    local endpoint="${1#/}"
    curl -s -X 'GET' "${HOST_URL}${endpoint}" -H 'accept: application/json'
}

# Usage: _api_post "/endpoint" | "endpoint" '{"json": "data"}'
_api_post() {
    local endpoint="${1#/}"
    curl -s -o /dev/null -X 'POST' "${HOST_URL}${endpoint}" \
        -H 'Content-Type: application/json' \
        -H 'accept: application/json' \
        -d "$2"
}

# Usage: _api_delete "/endpoint" | "endpoint"
_api_delete() {
    local endpoint="${1#/}"
    curl -s -o /dev/null -X 'DELETE' "${HOST_URL}${endpoint}" -H 'accept: application/json'
}

# Usage: _api_status "GET" "/endpoint" | "endpoint"
_api_status() {
    local method="$1"
    local endpoint="${2#/}"
    curl -s -o /dev/null -w "%{http_code}" -X "$method" "${HOST_URL}${endpoint}" -H 'accept: application/json'
}

# Special wrapper for root endpoints like /health, /docs
_root_status() {
    local method="$1"
    local endpoint="${2#/}"
    curl -s -o /dev/null -w "%{http_code}" -X "$method" "${ROOT_URL}/${endpoint}" -H 'accept: application/json'
}

# Usage: _api_download "/endpoint" | "endpoint" "filename.ext"
_api_download() {
    local status
    local curl_exit
    local endpoint="${1#/}"

    status=$(curl -s -w "%{http_code}" -X 'GET' "${HOST_URL}${endpoint}" -o "$OUT_DIR/$2")
    curl_exit=$?

    if [[ "$status" == "200" && "$curl_exit" -eq 0 ]]; then
        return 0
    else
        rm -f "$OUT_DIR/$2"
        return 1
    fi
}

# --- API Demo Visual Wrappers ---
_demo_get() {
    # Added -L to follow redirects
    local response
    response=$(curl -sL -X 'GET' "${HOST_URL}$1" -H 'accept: application/json')
    if [ -n "$response" ]; then
        echo "$response" | python3 -m json.tool
    else
        echo -e "${RED}Error: Received empty response from server.${NC}"
    fi
}

_demo_post() {
    # Added -L to follow redirects
    local response
    response=$(curl -sL -X 'POST' "${HOST_URL}$1" \
        -H 'Content-Type: application/json' \
        -H 'accept: application/json' \
        -d "$2")
    if [ -n "$response" ]; then
        echo "$response" | python3 -m json.tool
    else
        echo -e "${RED}Error: Received empty response from server.${NC}"
    fi
}

_demo_patch() {
    # Added -L to follow redirects
    local response
    response=$(curl -sL -X 'PATCH' "${HOST_URL}$1" \
        -H 'Content-Type: application/json' \
        -H 'accept: application/json' \
        -d "$2")
    if [ -n "$response" ]; then
        echo "$response" | python3 -m json.tool
    else
        echo -e "${RED}Error: Received empty response from server.${NC}"
    fi
}


# Usage: assert_api "GET" "/endpoint" "200" "Success msg" "Error msg"
assert_api() {
    local method="$1"
    local endpoint="$2"
    local expected_status="$3"
    local success_msg="$4"
    local error_msg="$5"

    local status=$(_api_status "$method" "$endpoint")
    if [[ "$status" == "$expected_status" ]]; then
        [ -n "$success_msg" ] && log_success "$success_msg"
    else
        [ -n "$error_msg" ] && log_error "$error_msg (HTTP $status)"
        exit 1
    fi
}

# Usage: assert_api "GET" "/health" "200" "Success msg" "Error msg"
assert_root_api() {
    local method="$1"
    local endpoint="$2"
    local expected_status="$3"
    local success_msg="$4"
    local error_msg="$5"

    local status=$(_root_status "$method" "$endpoint")
    if [[ "$status" == "$expected_status" ]]; then
        [ -n "$success_msg" ] && log_success "$success_msg"
    else
        [ -n "$error_msg" ] && log_error "$error_msg (HTTP $status)"
        exit 1
    fi
}

# --- Port Management ---
kill_ports() {
    header "PORT KILLER"
    for port in 8000 8080; do
        log_info "Checking Port $port..."
        if lsof -i :$port -t >/dev/null 2>&1; then
            log_warn "Port $port is in use. Killing process..."
            sudo lsof -i :$port -t | xargs sudo kill -9 2>/dev/null || true
            log_success "Port $port is free"
        else
            log_success "Port $port is free"
        fi
    done
}

# --- Service Operations ---
start() {
    if ask_yes_no "Would you like to check and kill conflicting ports (8000/8080)?"; then
        kill_ports
    fi

    header "FASTAPI SERVICE CREATION"
    log_info "Spinning up FastAPI container..."
    assert_cmd "Container started" "Failed to start FastAPI container" _compose_build_up api

    log_warn "Waiting for API readiness..."
    for i in {1..15}; do
        if [[ $(_root_status "GET" "/health") == "200" ]]; then
            log_success "FastAPI is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    log_error "Timed out waiting for FastAPI to boot"
    return 1
}

stop() {
    header "STOPPING FASTAPI"
    _compose_stop api
    log_success "FastAPI stopped"
}

run_local() {
    if ask_yes_no "Would you like to check and kill conflicting ports?"; then
        kill_ports
    fi
    header "LOCAL FASTAPI SERVER"
    log_info "Starting Uvicorn..."
    uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
}

# --- End-to-End Testing ---
diagnostics() {
    header "FASTAPI END-TO-END STATUS"

    log_info "Checking Health Endpoint..."
    assert_root_api "GET" "/health" "200" "Health OK" "Health check failed"

    log_info "Checking OpenAPI Docs..."
    assert_root_api "GET" "/docs" "200" "Docs OK" "Docs unreachable"

    log_info "Checking ReDoc..."
    assert_root_api "GET" "/redoc" "200" "Redocs OK" "Redocs unreachable"

    # Notice how we now just pass "companies" rather than "/api/v1/companies"
    log_info "Ingesting TESCO PLC (00445790)..."
    assert_cmd "Ingestion successful" "Tesco ingestion failed" _api_post "companies" '{"company_number": "00445790"}'
    echo

    log_info "Ingesting SHELL PLC (04366849)..."
    assert_cmd "Ingestion successful" "Shell ingestion failed" _api_post "companies" '{"company_number": "04366849"}'
    echo

    log_info "Submitting Primary ESG Metrics (Tesco - 2024)..."
    assert_cmd "Metrics added successfully" "Metrics submission failed" _api_post "companies/1/metrics" '{"reporting_year": 2024, "energy_consumption_mwh": 4500.5, "carbon_emissions_tco2e": 250.0, "water_usage_m3": 500.0, "waste_generated_tonnes": 120.5}'
    echo

    log_info "Verifying ESG Metrics Endpoint..."
    assert_api "GET" "companies/1/metrics" "200" "Metrics retrieved successfully" "Metrics retrieval failed"
    echo

    log_info "Simulating Green Loan (Tesco)..."
    assert_cmd "Simulation successful" "Simulation failed" _api_post "companies/1/simulate-loan" '{"loan_amount": 1000000, "term_months": 120}'
    echo

    log_info "Testing CSV Bulk Export..."
    assert_cmd "CSV Exported successfully to out/companies_export.csv" "CSV Export failed" _api_download "companies/export/csv" "companies_export.csv"

    log_info "Testing PDF Quote Generation..."
    assert_cmd "PDF Rendered successfully to out/green_loan_quote.pdf" "PDF Generation failed" _api_download "companies/1/simulate-loan/1/pdf" "green_loan_quote.pdf"

    log_info "Checking container logs..."
    _compose_logs api 5

    log_success "FastAPI status check complete."
}

prompt_next() {
    log_warn "\nPress enter to go to the next step..."; read -r
}

# --- Interactive System Demonstration ---
api_demo() {
    header "FULL SYSTEM DIAGNOSTIC & API DEMONSTRATION"

    log_info "Step 0: SYSTEM HEALTH & DOCS"
    assert_root_api "GET" "/health" "200" "Health OK" "Health check failed"
    assert_root_api "GET" "/docs" "200" "OpenAPI Docs OK" "Docs unreachable"
    assert_root_api "GET" "/redoc" "200" "ReDoc OK" "Redocs unreachable"
    prompt_next

    log_info "Step 1: CREATE (C) - Ingesting Corporate Entities"
    log_data "POST /companies/ (TESCO PLC)"

    # Capture the raw JSON response
    local tesco_res
    tesco_res=$(curl -sL -X 'POST' "${HOST_URL}companies" \
        -H 'Content-Type: application/json' \
        -H 'accept: application/json' \
        -d '{"company_number": "00445790"}')

    # Display it beautifully
    echo "$tesco_res" | python3 -m json.tool

    # Dynamically extract the newly assigned ID using Python
    COMPANY_ID=$(echo "$tesco_res" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")

    if [ -z "$COMPANY_ID" ] || [ "$COMPANY_ID" == "None" ]; then
        log_error "Failed to parse Company ID from response. Aborting."
        return 1
    fi
    log_success "Dynamically captured TESCO Company ID: $COMPANY_ID"

    echo
    log_data "POST /companies/ (SHELL PLC)"
    _demo_post "companies" '{"company_number": "04366849"}'
    prompt_next

    log_info "Step 2: READ (R) - Fetching Directory and Specific Entity"
    log_data "GET /companies/ (List all companies)"
    _demo_get "companies"

    echo
    log_data "GET /companies/$COMPANY_ID (Fetch TESCO specifically)"
    _demo_get "companies/$COMPANY_ID"
    prompt_next

    log_info "Step 3: UPDATE (U) - Patching Company Details (Updating Sector)"
    log_data "PATCH /companies/$COMPANY_ID"
    _demo_patch "companies/$COMPANY_ID" '{"business_sector": "Advanced Retail Logistics"}'
    prompt_next

    log_info "Step 4: ESG METRICS - Submitting and Verifying"
    log_data "POST /companies/$COMPANY_ID/metrics"
    _demo_post "companies/$COMPANY_ID/metrics" '{"reporting_year": 2024, "energy_consumption_mwh": 4500.5, "carbon_emissions_tco2e": 250.0, "water_usage_m3": 500.0, "waste_generated_tonnes": 120.5}'

    echo
    log_data "GET /companies/$COMPANY_ID/metrics (Verify insertion)"
    _demo_get "companies/$COMPANY_ID/metrics"
    prompt_next

    log_info "Step 5: ENGINE EXECUTION - Simulating Green Loan (SLL)"
    log_warn "This step triggers the algorithmic Margin Ratchet calculation."
    log_data "POST /companies/$COMPANY_ID/simulate-loan"

    # Capture the simulation response to extract the Simulation ID
    local sim_res
    sim_res=$(curl -sL -X 'POST' "${HOST_URL}companies/$COMPANY_ID/simulate-loan" \
        -H 'Content-Type: application/json' \
        -H 'accept: application/json' \
        -d '{"loan_amount": 2500000, "term_months": 60}')

    echo "$sim_res" | python3 -m json.tool
    SIM_ID=$(echo "$sim_res" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")

    log_success "Dynamically captured Simulation ID: $SIM_ID"
    prompt_next

    log_info "Step 6: BULK EXPORTS & FILES - CSV and PDF Generation"
    log_data "GET /companies/export/csv"
    assert_cmd "CSV Exported successfully to out/companies_export.csv" "CSV Export failed" _api_download "companies/export/csv" "companies_export.csv"

    echo
    log_data "GET /companies/$COMPANY_ID/simulate-loan/$SIM_ID/pdf"
    assert_cmd "PDF Rendered successfully to out/green_loan_quote.pdf" "PDF Generation failed" _api_download "companies/$COMPANY_ID/simulate-loan/$SIM_ID/pdf" "green_loan_quote.pdf"
    prompt_next

    log_info "Step 7: DELETE (D) - Hard-deleting the Company"
    log_warn "This will cascade and destroy the company, its metrics, and the loan simulation."
    log_data "DELETE /companies/$COMPANY_ID"
    local status=$(_api_status "DELETE" "companies/$COMPANY_ID")
    if [ "$status" = "204" ]; then
        log_success "Company Deleted (HTTP 204)"
    else
        log_error "Deletion Failed"
    fi
    prompt_next

    log_info "Step 8: VERIFICATION - Ensuring Referential Integrity (Cascading Deletes)"
    log_data "GET /companies/$COMPANY_ID (Checking Parent Company)"
    local verify_status=$(_api_status "GET" "companies/$COMPANY_ID")
    if [ "$verify_status" = "404" ]; then
        log_success "Verified: Parent Company is gone (HTTP 404)"
    else
        log_error "Company still exists!"
    fi

    log_data "GET /companies/$COMPANY_ID/metrics (Checking Cascaded Metrics)"
    local metric_status=$(_api_status "GET" "companies/$COMPANY_ID/metrics")
    if [ "$metric_status" = "404" ]; then
        log_success "Verified: Cascaded Metrics are gone (HTTP 404)"
    else
        log_error "Metrics still exist!"
    fi

    log_data "GET /companies/$COMPANY_ID/simulate-loan/$SIM_ID/pdf (Checking PDF Access)"
    local pdf_status=$(_api_status "GET" "companies/$COMPANY_ID/simulate-loan/$SIM_ID/pdf")
    if [ "$pdf_status" = "404" ]; then
        log_success "Verified: Simulation access blocked/deleted (HTTP 404)"
    else
        log_error "Simulation still accessible!"
    fi
    prompt_next

    log_info "Step 9: SYSTEM LOGS"
    log_info "Checking recent container logs for any silent errors..."
    _compose_logs api 5

    echo
    log_success "Full System Diagnostic, CRUD, and Execution Demonstration Complete!"
}

# --- Execution Entry ---
main() {
    load_env

    case "${1:-}" in
        start) start ;;
        stop) stop ;;
        status) diagnostics ;;
        demo) api_demo ;;
        run) run_local ;;
        kill) kill_ports ;;
        config) show_env ;;
        logs) docker logs -f "${API_CONTAINER}" ;;
        *)
            echo "Usage: $0 {start|stop|status|run|kill|config|logs}"
            echo
            echo "Commands:"
            log_info "start   - Build and start FastAPI container"
            log_info "stop    - Stop FastAPI container"
            log_info "status  - Run full E2E ingestion and diagnostic workflow"
            log_info "run     - Run locally using Uvicorn (hot-reload)"
            log_info "kill    - Kill processes using ports 8000/8080"
            log_info "config  - Show environment config"
            log_info "logs    - Tail container logs"
            exit 1
            ;;
    esac
}

main "$@"
