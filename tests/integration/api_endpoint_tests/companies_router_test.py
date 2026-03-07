# tests/integration/api_endpoint_tests/companies_router_test.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.api
async def test_create_company_success(async_client: AsyncClient, mock_oc_response_hsbc):
    """
    Hits the 'try' block and successful 'return company' using full stack execution.
    """
    # Patch httpx directly to simulate the entire service and client execution chain
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_oc_response_hsbc
        mock_get.return_value = mock_response

        # Execute the POST request against the FastAPI router
        response = await async_client.post(
            "/api/v1/companies/",
            json={"company_number": "09928412"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "HSBC UK BANK PLC"
        assert data["business_sector"] == "Banks"
        assert data["location"] == "Birmingham"
        mock_get.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.api
async def test_create_company_http_exception(async_client: AsyncClient):
    """
    Hits the 'except HTTPException' block
        by simulating a rate limit from the external API.
    """
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 403  # OpenCorporates returns 403 for Rate Limits
        mock_get.return_value = mock_response

        response = await async_client.post(
            "/api/v1/companies/",
            json={"company_number": "42942942"}
        )

        # The OpenCorporatesClient turns 403 into 429, and the router passes it through
        assert response.status_code == 429
        assert "rate limit exceeded" in response.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.api
async def test_create_company_generic_exception(async_client: AsyncClient):
    """Hits the 'except Exception' fallback block by breaking the service internally."""
    with patch(
        "app.services.company_service.CompanyService.register_company",
        new_callable=AsyncMock) as mock_reg:
        mock_reg.side_effect = Exception("Catastrophic Database Failure")

        response = await async_client.post(
            "/api/v1/companies/",
            json={"company_number": "50050050"}
        )

        assert response.status_code == 500
        assert "Catastrophic Database Failure" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.api
async def test_list_companies(async_client: AsyncClient, seed_companies):
    """Hits the DB query and scalars().all() return."""
    response = await async_client.get("/api/v1/companies/?skip=0&limit=10")
    assert response.status_code == 200
    assert len(response.json()) >= len(seed_companies)


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_cache_hit(async_client: AsyncClient, seed_companies):
    """Hits the 'if cached_company: return cached_company' block."""
    target_company = seed_companies[0]

    with patch(
        "app.api.v1.endpoints.companies.get_cached_object",
        new_callable=AsyncMock) as mock_cache:
        mock_cache.return_value = {
            "id": target_company.id,
            "companies_house_id": target_company.companies_house_id,
            "name": "Cached Version Corp",
            "business_sector": "IT",
            "location": "UK",
            "opencorporates_url": None
        }

        response = await async_client.get(f"/api/v1/companies/{target_company.id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Cached Version Corp"


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_db_fallback_and_not_found(
    async_client: AsyncClient,seed_companies):
    """Hits the DB fallback, cache population, and 404 Not Found blocks."""
    with patch(
        "app.api.v1.endpoints.companies.get_cached_object",
        new_callable=AsyncMock) as mock_cache:
        mock_cache.return_value = None

        # 1. DB Fallback (Cache Miss)
        response_success = await async_client.get(
            f"/api/v1/companies/{seed_companies[0].id}"
        )
        assert response_success.status_code == 200
        assert response_success.json()["name"] == seed_companies[0].name

        # 2. 404 Not Found
        response_not_found = await async_client.get("/api/v1/companies/99999")
        assert response_not_found.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_update_company_flows(async_client: AsyncClient, seed_companies):
    """Hits the dynamic update logic, db.commit, and cache invalidation."""
    target_id = seed_companies[0].id

    # 1. Successful Update
    response_update = await async_client.patch(
        f"/api/v1/companies/{target_id}", json={"location": "Global HQ"}
        )
    assert response_update.status_code == 200
    assert response_update.json()["location"] == "Global HQ"

    # 2. 404 Not Found
    response_not_found = await async_client.patch(
        "/api/v1/companies/99999", json={"location": "Nowhere"}
        )
    assert response_not_found.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_delete_company_flows(async_client: AsyncClient, seed_companies):
    """Hits the db.delete, db.commit, and cache purge."""
    target_id = seed_companies[2].id  # Use ID 3 to preserve previous entries

    # 1. Successful Delete
    response_delete = await async_client.delete(f"/api/v1/companies/{target_id}")
    assert response_delete.status_code == 204

    # 2. Verify 404 Not Found on subsequent request
    response_not_found = await async_client.delete("/api/v1/companies/99999")
    assert response_not_found.status_code == 404

# tests/integration/api_endpoint_tests/companies_router_test.py


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_db_hit_and_cache_set(
    async_client: AsyncClient, seed_companies):
    """
    Tests the DB fallback block:
    Proves that a cache miss hits the DB (scalars().first()),
    finds the company, and calls set_cached_object.
    """
    target = seed_companies[0]

    # We patch both the get (to force a miss) and the set (to spy on it)
    with patch(
        "app.api.v1.endpoints.companies.get_cached_object",
        new_callable=AsyncMock) as mock_get, \
            patch(
                "app.api.v1.endpoints.companies.set_cached_object",
                new_callable=AsyncMock) as mock_set:

        mock_get.return_value = None  # Force a cache miss

        response = await async_client.get(f"/api/v1/companies/{target.id}")

        assert response.status_code == 200
        assert response.json()["name"] == target.name
        # Proves the cache population block executed
        mock_set.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_not_found(async_client: AsyncClient):
    """Proves result.scalars().first() returns None and raises 404."""
    with patch(
        "app.api.v1.endpoints.companies.get_cached_object",
        new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        response = await async_client.get("/api/v1/companies/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Company not found"


@pytest.mark.asyncio
@pytest.mark.api
async def test_update_company_success_and_cache_invalidate(
    async_client: AsyncClient,
    seed_companies):
    """Tests successful PATCH, db.commit(), and cache invalidation."""
    target = seed_companies[0]

    # Spy on the cache invalidation function
    with patch(
        "app.api.v1.endpoints.companies.invalidate_cache",
        new_callable=AsyncMock) as mock_inv:
        response = await async_client.patch(
            f"/api/v1/companies/{target.id}",
            json={"location": "New Earth HQ"}
        )

        assert response.status_code == 200
        assert response.json()["location"] == "New Earth HQ"
        # Proves the cache was successfully purged
        mock_inv.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.api
async def test_update_company_not_found(async_client: AsyncClient):
    """Proves updating a non-existent company triggers the 404 HTTPException."""
    response = await async_client.patch(
        "/api/v1/companies/99999",
        json={"location": "Nowhere"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"


@pytest.mark.asyncio
@pytest.mark.api
async def test_delete_company_success_and_cache_invalidate(
    async_client: AsyncClient, seed_companies):
    """Tests successful DELETE, db.delete(), and cache invalidation."""
    target = seed_companies[1]  # Using second company to preserve state

    with patch(
        "app.api.v1.endpoints.companies.invalidate_cache",
        new_callable=AsyncMock) as mock_inv:
        response = await async_client.delete(f"/api/v1/companies/{target.id}")

        assert response.status_code == 204
        # Proves the cache was successfully purged after deletion
        mock_inv.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.api
async def test_delete_company_not_found(async_client: AsyncClient):
    """Proves deleting a non-existent company triggers the 404 HTTPException."""
    response = await async_client.delete("/api/v1/companies/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"
