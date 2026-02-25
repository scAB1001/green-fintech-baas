# tests/integration/health_test.py
import pytest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint_integration(async_client):
    # Ensure this matches your route!
    # If main.py has app.include_router(api_router, prefix="/api/v1")
    # You might need "/api/v1/health"
    response = await async_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data  # Validate that versioning is working
