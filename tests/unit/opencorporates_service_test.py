# tests/unit/opencorporates_service.py
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.services.opencorporates_service import OpenCorporatesClient


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_company_details_success(mock_oc_response_tesco):
    client = OpenCorporatesClient()
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_oc_response_tesco
        mock_get.return_value = mock_response

        result = await client.get_company_details("00445790")

        # TODO: Assert status codes and more.
        assert result["name"] == "TESCO PLC"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_company_details_not_found():
    client = OpenCorporatesClient()
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(HTTPException) as exc:
            await client.get_company_details("INVALID")
        assert exc.value.status_code == 404


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_company_details_rate_limit():
    """Verify HTTP 403 triggers a 429 Rate Limit exception."""
    client = OpenCorporatesClient()
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 403  # OpenCorporates returns 403 for rate limits
        mock_get.return_value = mock_response

        with pytest.raises(HTTPException) as exc:
            await client.get_company_details("00445790")
        assert exc.value.status_code == 429
        assert "rate limit exceeded" in exc.value.detail


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_company_details_server_error():
    """Verify HTTP 500 triggers a 502 Bad Gateway exception."""
    client = OpenCorporatesClient()
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with pytest.raises(HTTPException) as exc:
            await client.get_company_details("00445790")
        assert exc.value.status_code == 502


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_company_details_network_timeout():
    """Verify httpx.RequestError (like a timeout) is caught properly."""
    client = OpenCorporatesClient()
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Simulate a network drop/timeout
        mock_get.side_effect = httpx.RequestError("Connection timeout")

        with pytest.raises(HTTPException) as exc:
            await client.get_company_details("00445790")
        assert exc.value.status_code == 502
        assert "network error" in exc.value.detail
