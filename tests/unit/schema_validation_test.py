# tests/unit/company_schema_test.py
import pytest
from pydantic import ValidationError

from app.schemas.company_schema import CompanyCreateRequest
from app.schemas.environmental_metric_schema import EnvironmentalMetricCreate
from app.schemas.loan_simulation_schema import LoanSimulationCreate
from app.schemas.national_energy_schema import NationalEnergyBase
from app.schemas.regional_emission_schema import RegionalEmissionBase


@pytest.mark.unit
def test_company_house_id_boundaries():
    """Verify CH_ID strictly enforces the 8-character UK standard."""
    # 1. Valid (Exactly 8)
    valid_model = CompanyCreateRequest(company_number="12345678")
    assert valid_model.company_number == "12345678"

    # 2. Invalid (Too Short)
    with pytest.raises(ValidationError) as exc_info:
        CompanyCreateRequest(company_number="1234567")
    assert "String should have at least 8 characters" in str(exc_info.value)

    # 3. Invalid (Too Long)
    with pytest.raises(ValidationError) as exc_info:
        CompanyCreateRequest(company_number="123456789")
    assert "String should have at most 8 characters" in str(exc_info.value)


@pytest.mark.unit
def test_environmental_metric_boundaries():
    """Verify reporting years and non-negative metric constraints."""
    base_valid_data = {
        "company_id": 1,
        "reporting_year": 2025,
        "energy_consumption_mwh": 100.0,
        "carbon_emissions_tco2e": 50.0
    }

    # 1. Valid Boundaries (Year 2000, 0 emissions)
    valid_data = base_valid_data.copy()
    valid_data.update({"reporting_year": 2000, "carbon_emissions_tco2e": 0.0})
    valid_model = EnvironmentalMetricCreate(**valid_data)
    assert valid_model.reporting_year == 2000
    assert valid_model.carbon_emissions_tco2e == 0.0

    # 2. Invalid Year (Before 2000)
    with pytest.raises(ValidationError) as exc_info:
        invalid_year = base_valid_data.copy()
        invalid_year["reporting_year"] = 1999
        EnvironmentalMetricCreate(**invalid_year)
    assert "Input should be greater than or equal to 2000" in str(
        exc_info.value)

    # 3. Invalid Value (Negative Energy)
    with pytest.raises(ValidationError) as exc_info:
        invalid_energy = base_valid_data.copy()
        invalid_energy["energy_consumption_mwh"] = -1.5
        EnvironmentalMetricCreate(**invalid_energy)
    assert "Input should be greater than or equal to 0" in str(exc_info.value)


@pytest.mark.unit
def test_loan_simulation_boundaries():
    """Verify loan amounts and terms respect financial logic limits."""
    # 1. Valid Boundaries (1 month term)
    valid_model = LoanSimulationCreate(loan_amount=1000.0, term_months=1)
    assert valid_model.term_months == 1

    # 2. Valid Boundaries (Max 360 months / 30 years)
    valid_model_max = LoanSimulationCreate(loan_amount=1000.0, term_months=360)
    assert valid_model_max.term_months == 360

    # 3. Invalid Loan Amount (Zero or Negative)
    with pytest.raises(ValidationError):
        LoanSimulationCreate(loan_amount=0, term_months=60)

    # 4. Invalid Term (Over 30 years)
    with pytest.raises(ValidationError):
        LoanSimulationCreate(loan_amount=50000.0, term_months=361)


@pytest.mark.unit
def test_reference_data_year_boundaries():
    """Verify historical dataset years are bound between 1900 and 2100."""
    # 1. Valid Boundaries (National Energy)
    valid_energy = NationalEnergyBase(
        country="UK",
        energy_type="Solar",
        year=1900,
        energy_consumption=10,
        co2_emission=1
    )
    assert valid_energy.year == 1900

    # 2. Invalid Year (Regional Emission < 1900)
    with pytest.raises(ValidationError):
        RegionalEmissionBase(local_authority="Leeds", year=1899)

    # 3. Invalid Year (Regional Emission > 2100)
    with pytest.raises(ValidationError):
        RegionalEmissionBase(local_authority="Leeds", year=2101)
