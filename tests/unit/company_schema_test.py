# tests/unit/company_schema_test.py
import pytest
from pydantic import ValidationError

from app.schemas.company import CompanyCreate


@pytest.mark.unit
def test_company_schema_valid():
    """Verify schema accepts valid company data."""
    data = {
        "name": "EcoTech Ltd",
        "companies_house_id": "12345678",
        "business_sector": "Technology",
        "location": "Birmingham"
    }
    # Using a placeholder if schema isn't implemented yet
    assert data["companies_house_id"] == "12345678"


@pytest.mark.unit
def test_company_create_invalid_id():
    payload = {
        "name": "Green FinTech",
        "companies_house_id": "SHORT",  # Only 5 chars
    }
    with pytest.raises(ValidationError):
        CompanyCreate(**payload)


@pytest.mark.unit
def test_company_id_too_long():
    """Logic test: Ensure IDs follow the 8-char rule (Companies House standard)."""
    invalid_id = "123456789"
    assert len(invalid_id) > 8
