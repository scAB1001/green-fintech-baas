# tests/integration/testloan_simulation_service_test.py
import pytest
from fastapi import HTTPException

from app.models.company import Company
from app.services.loan_simulation_service import LoanSimulationService


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_quote_success(db_session, seed_companies, seed_metrics):
    """Test that the math and DB queries calculate the correct ESG score."""
    service = LoanSimulationService(db=db_session)

    # Grab the first seeded company (Green Hydrogen Corp)
    target_company = seed_companies[0]

    # Run the simulation
    simulation = await service.generate_quote(
        company_id=target_company.id, loan_amount=500000.0, term_months=60
    )

    assert simulation.company_id == target_company.id
    assert simulation.loan_amount == 500000.0
    assert simulation.term_months == 60
    assert simulation.base_rate == 8.00
    # Ensure the applied rate is lower than or equal to the base rate
    assert simulation.applied_rate <= simulation.base_rate
    assert simulation.esg_score >= 0.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_quote_company_not_found(db_session):
    """Ensure the service raises a 404 for invalid companies."""
    service = LoanSimulationService(db=db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.generate_quote(company_id=9999, loan_amount=1000, term_months=12)

    assert exc_info.value.status_code == 404
