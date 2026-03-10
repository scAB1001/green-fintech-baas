# tests/integration/api_endpoint_tests/companies_router_test.py
import base64
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.core.redis import get_redis_client
from app.main import app


@pytest.mark.asyncio
@pytest.mark.api
async def test_create_company_success(async_client: AsyncClient, mock_oc_response_hsbc):
    """
    Hits 'try' block and successful 'return company' using full stack execution.
    """
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_oc_response_hsbc
        mock_get.return_value = mock_response

        response = await async_client.post(
            "/api/v1/companies/", json={"company_number": "09928412"}
        )
        assert response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.api
async def test_create_company_http_exception(async_client: AsyncClient):
    """Hits the 'except HTTPException' block."""
    with patch(
        "app.services.company_service.CompanyService.register_company",
        new_callable=AsyncMock,
    ) as mock_reg:
        mock_reg.side_effect = HTTPException(status_code=429, detail="Rate limited")

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
    with patch(
        "" "app.services.company_service.CompanyService.register_company",
        new_callable=AsyncMock,
    ) as mock_reg:
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
    assert len(response.json()) <= len(seed_companies)


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_cache_hit(async_client: AsyncClient, seed_companies):
    """Hits the 'if cached_company: return cached_company' block."""
    target = seed_companies[0]
    with patch(
        "" "app.api.v1.endpoints.companies.get_cached_object", new_callable=AsyncMock
    ) as mock_cache:
        mock_cache.return_value = {
            "id": target.id,
            "companies_house_id": target.companies_house_id,
            "name": "Cached Version Corp",
            "business_sector": "IT",
            "location": "UK",
        }
        response = await async_client.get(f"/api/v1/companies/{target.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Cached Version Corp"


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_db_hit_and_cache_set(
    async_client: AsyncClient, seed_companies
):
    """Proves cache miss hits DB, finds company, and calls set_cached_object."""
    target = seed_companies[0]
    with (
        patch(
            "" "app.api.v1.endpoints.companies.get_cached_object",
            new_callable=AsyncMock,
        ) as mock_get,
        patch(
            "app.api.v1.endpoints.companies.set_cached_object", new_callable=AsyncMock
        ) as mock_set,
    ):

        mock_get.return_value = None  # Force Cache Miss

        response = await async_client.get(f"/api/v1/companies/{target.id}")
        assert response.status_code == 200
        # Proves the set_cached_object line was executed
        mock_set.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_company_not_found_404(async_client: AsyncClient):
    """Proves result.scalars().first() returning None triggers the 404 block."""
    with patch(
        "" "app.api.v1.endpoints.companies.get_cached_object", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = None
        response = await async_client.get("/api/v1/companies/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_update_company_success_and_cache_invalidate(
    async_client: AsyncClient, seed_companies
):
    """Tests successful PATCH, db.commit(), and cache invalidation execution."""
    target = seed_companies[0]
    with patch(
        "app.api.v1.endpoints.companies.invalidate_cache", new_callable=AsyncMock
    ) as mock_inv:
        response = await async_client.patch(
            f"/api/v1/companies/{target.id}", json={"location": "New Earth HQ"}
        )
        assert response.status_code == 200
        assert response.json()["location"] == "New Earth HQ"

        # Validates both the specific company cache and the CSV cache were purged
        assert mock_inv.call_count == 2
        mock_inv.assert_any_call(ANY, f"company:{target.id}")
        mock_inv.assert_any_call(ANY, "companies:csv")


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
    async_client: AsyncClient, seed_companies
):
    """Tests successful DELETE, db.delete(), and cache invalidation execution."""
    target = seed_companies[1]
    with patch(
        "app.api.v1.endpoints.companies.invalidate_cache", new_callable=AsyncMock
    ) as mock_inv:
        response = await async_client.delete(f"/api/v1/companies/{target.id}")
        assert response.status_code == 204

        # Validates both the specific company cache and the CSV cache were purged
        assert mock_inv.call_count == 2
        mock_inv.assert_any_call(ANY, f"company:{target.id}")
        mock_inv.assert_any_call(ANY, "companies:csv")


@pytest.mark.asyncio
@pytest.mark.api
async def test_delete_company_not_found_404(async_client: AsyncClient):
    """Proves deleting a non-existent company triggers the 404 HTTPException."""
    response = await async_client.delete("/api/v1/companies/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_export_companies_csv(async_client: AsyncClient, seed_companies):
    """Tests the text/csv generation endpoint."""
    response = await async_client.get("/api/v1/companies/export/csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert (
        'attachment; filename="companies_export.csv"'
        in response.headers["content-disposition"]
    )

    # Verify the CSV contains our seeded data
    csv_content = response.text
    assert "Company Number,Name,Sector,Location" in csv_content
    assert seed_companies[0].name in csv_content


@pytest.mark.asyncio
@pytest.mark.api
async def test_simulate_loan_internal_error(async_client: AsyncClient, seed_companies):
    """Test POST /companies/{id}/simulate-loan catches generic exceptions."""
    target_id = seed_companies[0].id

    # We force a failure by mocking the service to throw an exception
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


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_loan_simulation_pdf(
    async_client: AsyncClient, seed_companies, db_session
):
    """Tests the application/pdf generation endpoint."""
    target_company = seed_companies[0]

    # Seed a fake simulation for the test
    from app.models.loan_simulation import LoanSimulation

    sim = LoanSimulation(
        company_id=target_company.id,
        loan_amount=500000,
        term_months=60,
        base_rate=5.0,
        applied_rate=4.5,
        esg_score=75.0,
        estimated_carbon_savings=10.5,
    )
    db_session.add(sim)
    await db_session.commit()
    await db_session.refresh(sim)

    # 1. Test Successful PDF Generation
    response = await async_client.get(
        f"/api/v1/companies/{target_company.id}/simulate-loan/{sim.id}/pdf"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # All valid PDFs start with this byte signature
    assert response.content.startswith(b"%PDF-")

    # 2. Test Company Not Found
    response_no_company = await async_client.get(
        f"/api/v1/companies/99999/simulate-loan/{sim.id}/pdf"
    )
    assert response_no_company.status_code == 404

    # 3. Test Simulation Not Found
    response_no_sim = await async_client.get(
        f"/api/v1/companies/{target_company.id}/simulate-loan/99999/pdf"
    )
    assert response_no_sim.status_code == 404


@pytest.mark.asyncio
@pytest.mark.api
async def test_export_companies_csv_cache_hit(async_client: AsyncClient):
    """
    Proves the CSV endpoint returns cached text by injecting a mock Redis client.
    """
    fake_csv_data = "ID,Company Number,Name\n999,00000000,Cached Corp\n"

    # 1. Create a fake Redis client
    mock_redis = AsyncMock()
    mock_redis.get.return_value = fake_csv_data

    # 2. Create an async generator to match your get_redis_client signature
    async def override_get_redis():
        yield mock_redis

    # 3. Override the dependency in FastAPI
    app.dependency_overrides[get_redis_client] = override_get_redis

    try:
        response = await async_client.get("/api/v1/companies/export/csv")

        assert response.status_code == 200
        assert response.text == fake_csv_data
        mock_redis.get.assert_called_once_with("companies:csv")
    finally:
        # 4. ALWAYS clear the overrides so it doesn't pollute other tests!
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.api
async def test_get_loan_simulation_pdf_cache_hit(
    async_client: AsyncClient, seed_companies
):
    """
    Proves the PDF endpoint decodes the base64 cache by injecting a mock Redis client.
    """
    target = seed_companies[0]
    fake_pdf_bytes = b"%PDF-1.4 Fake Cached PDF Document"
    fake_b64 = base64.b64encode(fake_pdf_bytes).decode("utf-8")

    mock_redis = AsyncMock()
    mock_redis.get.return_value = fake_b64

    async def override_get_redis():
        yield mock_redis

    app.dependency_overrides[get_redis_client] = override_get_redis

    try:
        # We use simulation ID 1 assuming it exists from our seeded state
        response = await async_client.get(
            f"/api/v1/companies/{target.id}/simulate-loan/1/pdf"
        )

        assert response.status_code == 200
        assert response.content == fake_pdf_bytes
        mock_redis.get.assert_called_once_with("simulation:1:pdf")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.api
async def test_create_company_invalidates_patterns(
    async_client: AsyncClient, mock_oc_response_hsbc
):
    """
    Proves that a POST request successfully triggers pattern invalidation for lists.
    """
    with (
        patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get,
        patch(
            "app.api.v1.endpoints.companies.invalidate_pattern", new_callable=AsyncMock
        ) as mock_inv_pattern,
        patch(
            "app.api.v1.endpoints.companies.invalidate_cache", new_callable=AsyncMock
        ) as mock_inv_cache,
    ):

        # Setup the external API mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_oc_response_hsbc
        mock_get.return_value = mock_response

        response = await async_client.post(
            "/api/v1/companies/", json={"company_number": "09928412"}
        )

        assert response.status_code == 201

        # Prove the cache clearing functions were called with the correct arguments
        mock_inv_pattern.assert_called_once_with(ANY, "companies:list:*")
        mock_inv_cache.assert_called_once_with(ANY, "companies:csv")
