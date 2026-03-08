# tests/integration/api_endpoint_tests/health_api_test.py
import pytest


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
@pytest.mark.smoke
async def test_health_endpoint(async_client):
    """Smoke test to ensure the API is booting correctly."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.api
async def test_root_endpoint(async_client):
    """Verify root endpoint provides basic API info."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert "docs" in response.json()
