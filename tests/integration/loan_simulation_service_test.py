# tests/integration/loan_simulation_service_test.py
import pytest
from fastapi import HTTPException

from app.models.environmental_metric import EnvironmentalMetric
from app.models.national_energy import NationalEnergy
from app.models.regional_emission import RegionalEmission
from app.services.loan_simulation_service import LoanSimulationService


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_quote_fallback_proxy_data(db_session, seed_companies):
    """
    Test the simulation engine when NO company-specific metrics exist.
    It should fall back to a 70/30 weighting of Regional and National baselines.
    """
    target_company = seed_companies[0]  # Assuming this company has location "Leeds"

    # 1. Seed Reference Data
    regional = RegionalEmission(local_authority="Leeds", year=2024, grand_total=500.0)
    energy_total = NationalEnergy(
        country="United Kingdom",
        energy_type="all_energy_types",
        year=2024,
        energy_consumption=1000.0,
    )
    energy_renew = NationalEnergy(
        country="United Kingdom",
        energy_type="renewables_n_other",
        year=2024,
        energy_consumption=800.0,
    )
    db_session.add_all([regional, energy_total, energy_renew])
    await db_session.commit()

    # 2. Run Simulation
    service = LoanSimulationService(db=db_session)
    simulation = await service.generate_quote(
        company_id=target_company.id, loan_amount=500000.0, term_months=60
    )

    # 3. Assert Constraints
    assert simulation.company_id == target_company.id

    # 4. Mathematical Proof (Fallback Weighting)
    # S_nat = (800 / 1000) * 100 = 80.0
    # E_loc = 100 - ((500 / 5000) * 100) = 90.0
    # EPS = (80.0 * 0.3) + (90.0 * 0.7) = 87.0
    assert simulation.esg_score == 87.0

    # Capital deployed proxy calculation: (87.0 / 100) * (500000 / 1000) = 435.0
    assert simulation.estimated_carbon_savings == 435.0
    assert simulation.applied_rate < simulation.base_rate


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_quote_with_primary_company_data(db_session, seed_companies):
    """
    Test the simulation engine when actual company metrics DO exist.
    It should shift to a 50/20/30 weighting prioritizing the primary data.
    """
    target_company = seed_companies[0]

    # 1. Seed Reference Data
    regional = RegionalEmission(local_authority="Leeds", year=2024, grand_total=500.0)
    energy_total = NationalEnergy(
        country="United Kingdom",
        energy_type="all_energy_types",
        year=2024,
        energy_consumption=1000.0,
    )
    energy_renew = NationalEnergy(
        country="United Kingdom",
        energy_type="renewables_n_other",
        year=2024,
        energy_consumption=800.0,
    )

    # 2. Seed Primary Company Data (This triggers the weighting shift)
    company_metric = EnvironmentalMetric(
        company_id=target_company.id,
        reporting_year=2024,
        energy_consumption_mwh=120.0,
        carbon_emissions_tco2e=250.0,  # Used to calculate C_score
    )

    db_session.add_all([regional, energy_total, energy_renew, company_metric])
    await db_session.commit()

    # 3. Run Simulation
    service = LoanSimulationService(db=db_session)
    simulation = await service.generate_quote(
        company_id=target_company.id, loan_amount=500000.0, term_months=60
    )

    # 4. Mathematical Proof (Primary Data Weighting)
    # S_nat = (800 / 1000) * 100 = 80.0
    # E_loc = 100 - ((500 / 5000) * 100) = 90.0
    # C_score = 100 - ((250 / 500) * 100) = 50.0
    # EPS = (80.0 * 0.30) + (90.0 * 0.20) + (50.0 * 0.50) = 24.0 + 18.0 + 25.0 = 67.0
    assert simulation.esg_score == 67.0

    # Real emissions proxy calculation: 250.0 * (67.0 / 100) * 0.10 = 16.75
    assert simulation.estimated_carbon_savings == 16.75

    # Rate Check: 8.00 - (67.0 / 100 * 2.50) = 6.325 -> rounded to 6.32/6.33
    assert simulation.applied_rate < simulation.base_rate


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_quote_company_not_found(db_session):
    """Ensure the service raises a 404 for invalid companies."""
    service = LoanSimulationService(db=db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.generate_quote(company_id=9999, loan_amount=1000, term_months=12)

    assert exc_info.value.status_code == 404
