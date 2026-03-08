# tests/integration/loan_simulation_service_test.py
import pytest
from fastapi import HTTPException

from app.models.national_energy import NationalEnergy
from app.models.regional_emission import RegionalEmission
from app.services.loan_simulation_service import LoanSimulationService


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_quote_success_with_reference_data(
    db_session,
    seed_companies
):
    """
    Test that the DB queries successfully fetch reference data for the math engine.
    """
    target_company = seed_companies[0]  # Has location "Leeds"

    # 1. Seed the required reference data for "Leeds" and "United Kingdom"
    regional = RegionalEmission(
        local_authority="Leeds", year=2024, grand_total=500.0
    )
    energy_total = NationalEnergy(
        country="United Kingdom",
        energy_type="all_energy_types",
        year=2024,
        energy_consumption=1000.0
    )
    energy_renew = NationalEnergy(
        country="United Kingdom",
        energy_type="renewables_n_other",
        year=2024,
        energy_consumption=800.0
    )
    db_session.add_all([regional, energy_total, energy_renew])
    await db_session.commit()

    # 2. Run the simulation
    service = LoanSimulationService(db=db_session)
    simulation = await service.generate_quote(
        company_id=target_company.id, loan_amount=500000.0, term_months=60
    )

    # 3. Verify the database pipeline worked
    assert simulation.company_id == target_company.id
    assert simulation.loan_amount == 500000.0

    # 4. Mathematically prove the discount was applied based on the seeded data
    # S_nat = (800 / 1000) * 100 = 80
    # E_loc = 100 - ((500 / 5000) * 100) = 90
    # EPS = (80 * 0.3) + (90 * 0.7) = 87.0
    assert simulation.esg_score == 87.0
    assert simulation.applied_rate < simulation.base_rate


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_quote_company_not_found(db_session):
    """Ensure the service raises a 404 for invalid companies."""
    service = LoanSimulationService(db=db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.generate_quote(
            company_id=9999, loan_amount=1000, term_months=12
        )

    assert exc_info.value.status_code == 404
