# tests/integration/company_crud_test.py
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.company import Company
from app.models.environmental_metric import EnvironmentalMetric
from app.models.loan_simulation import LoanSimulation
from app.models.national_energy import NationalEnergy
from app.models.regional_emission import RegionalEmission


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.crud
async def test_company_lifecycle(db_session):
    """Verify the full Create, Read, and Update lifecycle of a Company."""
    # 1. Create
    company = Company(
        name="Lifecycle Corp",
        companies_house_id="LIFE0001",
        business_sector="FinTech",
        location="Leeds",
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)

    assert company.id is not None
    assert company.name == "Lifecycle Corp"

    # 2. Update
    company.location = "London"
    await db_session.commit()

    # 3. Read & Verify Update
    stmt = select(Company).where(Company.companies_house_id == "LIFE0001")
    result = await db_session.execute(stmt)
    db_company = result.scalar_one()

    assert db_company.location == "London"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.crud
async def test_relationship_cascade_delete(db_session):
    """
    Verify that deleting a Company automatically orphans and deletes
    its attached EnvironmentalMetrics and LoanSimulations.
    """
    # 1. Create Parent
    company = Company(
        name="Cascade Corp",
        companies_house_id="CASC0001",
        business_sector="Manufacturing",
        location="Manchester",
    )
    db_session.add(company)
    await db_session.flush()

    # 2. Create Children
    metric = EnvironmentalMetric(
        company_id=company.id,
        reporting_year=2025,
        energy_consumption_mwh=100.0,
        carbon_emissions_tco2e=50.0,
    )
    simulation = LoanSimulation(
        company_id=company.id,
        loan_amount=1000000.0,
        term_months=120,
        base_rate=8.0,
        applied_rate=6.5,
        esg_score=85.0,
    )
    db_session.add_all([metric, simulation])
    await db_session.commit()

    metric_id = metric.id
    sim_id = simulation.id

    # 3. Delete Parent
    await db_session.delete(company)
    await db_session.commit()

    # 4. Prove Children were cleanly wiped out (Cascade success)
    metric_check = await db_session.get(EnvironmentalMetric, metric_id)
    sim_check = await db_session.get(LoanSimulation, sim_id)

    assert metric_check is None
    assert sim_check is None


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.crud
async def test_company_unique_constraint(db_session):
    """Verify the database rejects duplicate Companies House IDs."""
    company1 = Company(
        name="First Corp",
        companies_house_id="DUPE1234",
        business_sector="Tech",  # <--- Added to satisfy NOT NULL
        location="Leeds",
    )
    db_session.add(company1)
    await db_session.commit()

    company2 = Company(
        name="Second Corp",
        companies_house_id="DUPE1234",
        business_sector="Tech",  # <--- Added to satisfy NOT NULL
        location="London",
    )
    db_session.add(company2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()  # Clean up the failed transaction state


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.crud
async def test_environmental_metric_unique_constraint(db_session):
    """Verify a company cannot have two metrics for the same reporting year."""
    company = Company(
        name="Metric Corp",
        companies_house_id="METR0001",
        business_sector="Finance",  # <--- Added to satisfy NOT NULL
        location="Bristol",
    )
    db_session.add(company)
    await db_session.flush()

    metric1 = EnvironmentalMetric(
        company_id=company.id, reporting_year=2025, energy_consumption_mwh=10.0
    )
    db_session.add(metric1)
    await db_session.commit()

    metric2 = EnvironmentalMetric(
        company_id=company.id, reporting_year=2025, energy_consumption_mwh=20.0
    )
    db_session.add(metric2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.crud
async def test_reference_data_persistence(db_session):
    """Verify that standalone reference tables can be written and read."""
    # 1. National Energy
    energy = NationalEnergy(
        country="United Kingdom",
        energy_type="Solar",
        year=2024,
        energy_consumption=50.5,
        co2_emission=0.0,
    )
    db_session.add(energy)

    # 2. Regional Emission
    emission = RegionalEmission(local_authority="Leeds", year=2024, grand_total=1250.5)
    db_session.add(emission)
    await db_session.commit()

    # 3. Read back
    assert energy.id is not None
    assert emission.id is not None

    saved_emission = await db_session.get(RegionalEmission, emission.id)
    assert saved_emission.local_authority == "Leeds"
