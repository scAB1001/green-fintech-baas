# tests/integration/api_endpoint_tests/companies_router_test.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.api
async def test_create_company_success(
    async_client: AsyncClient, mock_oc_response_hsbc):
    """
    Hits the 'try' block and successful 'return company' using full stack execution.
    """
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_oc_response_hsbc
        mock_get.return_value = mock_response

        response = await async_client.post(
            "/api/v1/companies/",
            json={"company_number": "09928412"}
        )
        assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.api
async def test_create_company_http_exception(async_client: AsyncClient):
    """Hits the 'except HTTPException' block."""
    with patch(
        "app.services.company_service.CompanyService.register_company",
        new_callable=AsyncMock) as mock_reg:
        mock_reg.side_effect = HTTPException(
            status_code=429, detail="Rate limited")

        # Valid 8-char ID to pass Pydantic and reach the router
        response = await async_client.post(
            "/api/v1/companies/", json={"company_number": "42942942"}
        )

        assert response.status_code == 429
        assert response.json()["detail"] == "Rate limited"


@pytest.mark.asyncio
@pytest.mark.api
async def test_create_company_generic_exception(async_client: AsyncClient):
    """Hits the 'except Exception' fallback block."""
    with patch("" \
    "app.services.company_service.CompanyService.register_company",
    new_callable=AsyncMock) as mock_reg:
        mock_reg.side_effect = Exception("Catastrophic Database Failure")

        # Valid 8-char ID to pass Pydantic and reach the router
        response = await async_client.post(
            "/api/v1/companies/", json={"company_number": "50050050"}
        )

        assert response.status_code == 500
        assert "Catastrophic Database Failure" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.api
async def test_list_companies_pagination(async_client: AsyncClient, seed_companies):
    """Hits the offset/limit DB query and scalars().all() return."""
    response = await async_client.get("/api/v1/companies/?skip=0&limit=10")
    assert response.status_code == 200
    assert len(response.json()) >= len(seed_companies)


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_cache_hit(async_client: AsyncClient, seed_companies):
    """Hits the 'if cached_company: return cached_company' block."""
    target = seed_companies[0]
    with patch("" \
    "app.api.v1.endpoints.companies.get_cached_object",
    new_callable=AsyncMock) as mock_cache:
        mock_cache.return_value = {
            "id": target.id,
            "companies_house_id": target.companies_house_id,
            "name": "Cached Version Corp",
            "business_sector": "IT",
            "location": "UK"
        }
        response = await async_client.get(f"/api/v1/companies/{target.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Cached Version Corp"


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_db_hit_and_cache_set(
        async_client: AsyncClient, seed_companies):
    """Proves cache miss hits DB, finds company, and calls set_cached_object."""
    target = seed_companies[0]
    with patch("" \
    "app.api.v1.endpoints.companies.get_cached_object",
    new_callable=AsyncMock) as mock_get, \
            patch(
                "app.api.v1.endpoints.companies.set_cached_object",
                new_callable=AsyncMock) as mock_set:

        mock_get.return_value = None  # Force Cache Miss

        response = await async_client.get(f"/api/v1/companies/{target.id}")
        assert response.status_code == 200
        # Proves the set_cached_object line was executed
        mock_set.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_not_found_404(async_client: AsyncClient):
    """Proves result.scalars().first() returning None triggers the 404 block."""
    with patch("" \
    "app.api.v1.endpoints.companies.get_cached_object",
    new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = await async_client.get("/api/v1/companies/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_update_company_success_and_cache_invalidate(
    async_client: AsyncClient, seed_companies):
    """Tests successful PATCH, db.commit(), and cache invalidation execution."""
    target = seed_companies[0]
    with patch(
        "app.api.v1.endpoints.companies.invalidate_cache",
        new_callable=AsyncMock) as mock_inv:
        response = await async_client.patch(
            f"/api/v1/companies/{target.id}",
            json={"location": "New Earth HQ"}
        )
        assert response.status_code == 200
        assert response.json()["location"] == "New Earth HQ"
        mock_inv.assert_called_once()  # Proves invalidate_cache was executed


@pytest.mark.asyncio
@pytest.mark.api
async def test_update_company_not_found_404(async_client: AsyncClient):
    """Proves updating a non-existent company triggers the 404 HTTPException."""
    response = await async_client.patch(
        "/api/v1/companies/99999", json={"location": "Nowhere"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_delete_company_success_and_cache_invalidate(
    async_client: AsyncClient, seed_companies):
    """Tests successful DELETE, db.delete(), and cache invalidation execution."""
    target = seed_companies[1]
    with patch(
        "app.api.v1.endpoints.companies.invalidate_cache",
        new_callable=AsyncMock) as mock_inv:
        response = await async_client.delete(f"/api/v1/companies/{target.id}")
        assert response.status_code == 204
        mock_inv.assert_called_once()  # Proves invalidate_cache was executed


@pytest.mark.asyncio
@pytest.mark.api
async def test_delete_company_not_found_404(async_client: AsyncClient):
    """Proves deleting a non-existent company triggers the 404 HTTPException."""
    response = await async_client.delete("/api/v1/companies/99999")
    assert response.status_code == 404
