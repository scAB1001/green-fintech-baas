"""
Authentication and API Key Integration Tests.

Validates the X-API-Key header security perimeter applied to the V1 routers.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app

# Apply the API marker so this runs with the endpoint test suite
pytestmark = pytest.mark.api

@pytest.mark.api
@pytest.mark.auth
async def test_missing_api_key_header():
    """
    Test that a request entirely missing the X-API-Key header
    is rejected with a 401 Unauthorized status.
    """
    # Create a raw client without the fixture's injected headers
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver") as raw_client:
        response = await raw_client.get("/api/v1/companies/")

        assert response.status_code == 401
        assert response.json() == {"detail": "Missing X-API-Key header"}


@pytest.mark.api
@pytest.mark.auth
async def test_invalid_api_key_header():
    """
    Test that a request with an incorrect X-API-Key header
    is rejected with a 401 Unauthorized status.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver") as raw_client:
        # Explicitly inject a known bad key
        response = await raw_client.get(
            "/api/v1/companies/",
            headers={"X-API-Key": "sk_fake_invalid_key_999999999"}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid API Key"}


@pytest.mark.api
@pytest.mark.auth
async def test_valid_api_key_header(async_client: AsyncClient):
    """
    Test that a request with the correct X-API-Key header is accepted.
    Utilizes the global async_client fixture which automatically injects
    the valid settings.API_KEY header.
    """
    response = await async_client.get("/api/v1/companies/")

    # We expect a 200 OK because the auth dependency passes.
    # Depending on the test database state, it will return a list.
    assert response.status_code == 200
    assert isinstance(response.json(), list)
