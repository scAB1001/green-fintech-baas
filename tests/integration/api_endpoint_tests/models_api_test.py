# tests/integration/api_endpoint_tests/companies_api_test.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.api
async def test_list_companies(async_client: AsyncClient, seed_companies):
    """Test GET /companies returns paginated data."""
    response = await async_client.get("/api/v1/companies/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(seed_companies)
    assert data[0]["name"] == "Green Hydrogen Corp"


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_by_id(async_client: AsyncClient, seed_companies):
    """Test GET /companies/{id} retrieves the correct entity."""
    target_id = seed_companies[0].id
    response = await async_client.get(f"/api/v1/companies/{target_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == target_id
    assert data["companies_house_id"] == "GH123456"


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/v1/companies/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_simulate_loan_endpoint(async_client: AsyncClient, seed_companies):
    """Test the POST /companies/{id}/simulate-loan endpoint."""
    target_id = seed_companies[0].id
    payload = {
        "loan_amount": 1000000.0,
        "term_months": 120
    }

    response = await async_client.post(
        f"/api/v1/companies/{target_id}/simulate-loan",
        json=payload
    )

    assert response.status_code == 201
    data = response.json()
    assert data["company_id"] == target_id
    assert data["applied_rate"] < data["base_rate"]
