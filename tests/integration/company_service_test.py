# tests/integration/company_service_test.py
from unittest.mock import AsyncMock, patch

import pytest

from app.services.company_service import CompanyService


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_company_already_exists(db_session, seed_companies):
    """
    Path 1: Test that existing companies return instantly
        without calling the external API.
    """
    mock_cache = AsyncMock()
    service = CompanyService(db=db_session, cache=mock_cache)

    existing_ch_id = seed_companies[0].companies_house_id

    # We patch the OpenCorporates client to ensure it is NEVER called
    with patch.object(service.oc_client, "get_company_details") as mock_oc:
        company = await service.register_company(existing_ch_id)

        assert company.id == seed_companies[0].id
        assert company.companies_house_id == existing_ch_id
        mock_oc.assert_not_called()  # Crucial: Proves we saved API rate limits


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_company_new_clean_data(db_session):
    """
    Path 2: Test that a new company is fetched, transformed, and persisted perfectly.
    """
    mock_cache = AsyncMock()
    service = CompanyService(db=db_session, cache=mock_cache)

    mock_oc_data = {
        "company_number": "CLEAN123",
        "name": "Clean Data Ltd",
        "industry_codes": [{"industry_code": {"description": "Software"}}],
        "registered_address": {"locality": "Edinburgh"},
        "opencorporates_url": "https://opencorporates.com/companies/gb/CLEAN123",
    }

    with patch.object(
        service.oc_client, "get_company_details", new_callable=AsyncMock
    ) as mock_oc:
        mock_oc.return_value = mock_oc_data

        company = await service.register_company("CLEAN123")

        assert company.id is not None
        assert company.name == "Clean Data Ltd"
        assert company.business_sector == "Software"
        assert company.location == "Edinburgh"
        mock_oc.assert_called_once_with("CLEAN123")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_register_company_dirty_data(db_session):
    """
    Path 3: Test fetching a company with missing/null data
        to trigger the 'Unknown' fallbacks.
    """
    mock_cache = AsyncMock()
    service = CompanyService(db=db_session, cache=mock_cache)

    # Simulate the exact scenario that crashed SHELL PLC earlier
    mock_oc_data = {
        "company_number": "DIRTY999",
        "name": "Dirty Data Corp",
        "industry_codes": None,  # Explicitly None to trigger the 'or []' fallback
        # Explicitly None to trigger 'or "Unknown"'
        "registered_address": {"locality": None},
        "opencorporates_url": "https://opencorporates.com/companies/gb/DIRTY999",
    }

    with patch.object(
        service.oc_client, "get_company_details", new_callable=AsyncMock
    ) as mock_oc:
        mock_oc.return_value = mock_oc_data

        company = await service.register_company("DIRTY999")

        assert company.id is not None
        assert company.name == "Dirty Data Corp"
        # Verify the fallbacks worked and prevented a database crash
        assert company.business_sector == "Unknown"
        assert company.location == "Unknown"
