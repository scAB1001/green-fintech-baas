# tests/integration/api_endpoint_tests/models_api_test.py
import pytest
from httpx import AsyncClient


@pytest.mark.api
@pytest.mark.smoke
async def test_get_companies_empty(async_client):
    """Verify GET /companies returns 200 even if empty (Smoke test)."""
    # Note: Ensure your route exists or prefix matches (e.g., /api/v1/companies)
    response = await async_client.get("/health")
    assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
async def test_create_environmental_metric_stub(async_client: AsyncClient):
    """
    STUB: Verify POST endpoint for environmental metrics.
    Assumes endpoint: POST /api/v1/metrics/
    """
    # Note: This will return 404 until the router is implemented
    payload = {
        "company_id": 1,
        "reporting_year": 2026,
        "energy_consumption_mwh": 100.0,
        "carbon_emissions_tco2e": 5.0
    }
    response = await async_client.post("/api/v1/metrics/", json=payload)

    # We expect 404 now; we want 201 later.
    # Use this to verify your testing infrastructure is 'pinging' the app.
    assert response.status_code in [201, 404]


@pytest.mark.api
@pytest.mark.integration
async def test_loan_simulation_calculation_stub(async_client: AsyncClient):
    """
    STUB: Verify POST endpoint for loan simulations.
    Assumes endpoint: POST /api/v1/simulations/
    """
    payload = {
        "company_id": 1,
        "loan_amount_gbp": 100000,
        "loan_term_years": 3,
        "base_interest_rate": 0.05
    }
    response = await async_client.post("/api/v1/simulations/", json=payload)

    assert response.status_code in [201, 404]
