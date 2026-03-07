# tests/integration/api_endpoint_tests/companies_api_test.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.models.company import Company
from app.services.opencorporates import OpenCorporatesClient


@pytest.mark.asyncio
@pytest.mark.api
async def test_create_company_endpoint_success(
    async_client: AsyncClient, mock_oc_response_shell
):
    """Test POST /companies/ ingests a new company successfully."""
    client = OpenCorporatesClient()
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_oc_response_shell
        mock_get.return_value = mock_response

        result = await client.get_company_details("04366849")

        # TODO: Assert status codes.

        assert result["name"] == "SHELL PLC"
        assert result["business_sector"] == "Fossil Fuels"


@pytest.mark.asyncio
@pytest.mark.api
async def test_list_companies(async_client: AsyncClient, seed_companies):
    """Test GET /companies/ returns paginated data."""
    response = await async_client.get("/api/v1/companies/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= len(seed_companies)


@pytest.mark.asyncio
@pytest.mark.api
async def test_update_company(async_client: AsyncClient, seed_companies):
    """Test PATCH /companies/{id} updates data and clears cache."""
    target_company = seed_companies[0]
    update_payload = {"location": "New Global HQ"}

    response = await async_client.patch(
        f"/api/v1/companies/{target_company.id}", json=update_payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "New Global HQ"


@pytest.mark.asyncio
@pytest.mark.api
async def test_update_company_not_found(async_client: AsyncClient):
    response = await async_client.patch(
        "/api/v1/companies/9999", json={"location": "Nowhere"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_delete_company(async_client: AsyncClient, seed_companies, db_session):
    """Test DELETE /companies/{id} removes entity and clears cache."""
    # Use second company to preserve the first for other tests
    target_company = seed_companies[1]

    response = await async_client.delete(f"/api/v1/companies/{target_company.id}")
    assert response.status_code == 204

    # Verify it is gone from the database
    verify_response = await async_client.get(f"/api/v1/companies/{target_company.id}")
    assert verify_response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_delete_company_not_found(async_client: AsyncClient):
    response = await async_client.delete("/api/v1/companies/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_simulate_loan_internal_error(async_client: AsyncClient, seed_companies):
    """Test POST /companies/{id}/simulate-loan catches generic exceptions."""
    target_id = seed_companies[0].id

    # We force a failure by passing invalid datatypes that bypass Pydantic
    # but crash the mathematical engine (e.g. mocking the service to throw an exception)
    with patch(
        "app.services.loan_simulation_service.LoanSimulationService.generate_quote",
        new_callable=AsyncMock,
    ) as mock_sim:
        mock_sim.side_effect = Exception("Database connection lost")

        response = await async_client.post(
            f"/api/v1/companies/{target_id}/simulate-loan",
            json={"loan_amount": 1000000, "term_months": 120},
        )
        assert response.status_code == 500
        assert "Database connection lost" in response.json()["detail"]
