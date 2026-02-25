# tests/integration/company_crud_test.py
import pytest
from sqlalchemy import select

from app.models.company import Company

# Import to register with Base
from app.models.environmental_metric import EnvironmentalMetric

# Import to register with Base
from app.models.loan_simulation import LoanSimulation


@pytest.mark.integration
@pytest.mark.crud
async def test_create_company_model(db_session):
    """Verify we can persist a Company model to the Postgres container."""
    new_company = Company(
        name="Green Hydrogen Corp",
        companies_house_id="GH123456",
        business_sector="Energy",
        location="Leeds"
    )
    db_session.add(new_company)
    await db_session.flush()  # Sync with DB but don't commit yet

    # Query it back
    stmt = select(Company).where(Company.companies_house_id == "GH123456")
    result = await db_session.execute(stmt)
    db_company = result.scalar_one()

    assert db_company.id is not None
    assert db_company.name == "Green Hydrogen Corp"


@pytest.mark.integration
@pytest.mark.crud
async def test_environmental_metric_relationship(db_session):
    """Verify relationship between Company and EnvironmentalMetric."""

    # Create parent
    company = Company(
        name="Test Corp",
        companies_house_id="TC000001",
        business_sector="Technology",  # Added
        location="London"             # Added
    )
    db_session.add(company)
    await db_session.flush()

    # Create child
    metric = EnvironmentalMetric(
        company_id=company.id,
        reporting_year=2025,
        energy_consumption_mwh=450.50,
        carbon_emissions_tco2e=12.5
    )
    db_session.add(metric)
    await db_session.flush()

    assert metric.company_id == company.id
