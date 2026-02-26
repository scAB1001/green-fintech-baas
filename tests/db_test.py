"""Test DB Statistics."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload  # For async relationships

from app.models.company import Company
from app.models.environmental_metric import EnvironmentalMetric


@pytest.mark.integration
@pytest.mark.smoke
async def test_inspect_database_contents(db_session, seed_companies, seed_metrics):
    """
    Diagnostic test to print the current state of the database.
    Exec: pytest -m integration -s tests/db_test.py
    """
    print("\n" + "="*60)
    print("DATABASE INSPECTION REPORT")
    print("="*60)

    # 1. Fetch Companies with EnvironmentalMetrics eagerly loaded
    # Prevents the "MissingGreenlet" error when accessing c.environmental_metrics
    stmt = select(Company).options(selectinload(Company.environmental_metrics))
    result = await db_session.execute(stmt)
    companies = result.scalars().all()

    print(f"\n[Companies Table] - Total: {len(companies)}")
    print(f"{'ID':<4} | {'CH_ID':<10} | {'Name':<20} | {'Sector':<15}")
    print("-" * 60)

    for c in companies:
        print(f"""{c.id:<4} | {c.companies_house_id:<10} |
              {c.name[:20]:<20} | {c.business_sector or 'N/A':<15}""")

    # 2. Detailed Relationship View
    print("\n" + "="*60)
    print("DETAILED RELATIONSHIP VIEW")
    print("="*60)

    for c in companies:
        print(f"\n🏢 COMPANY: {c.name} (ID: {c.id})")
        if not c.environmental_metrics:
            print("  (No metrics found)")
            continue

        print(f"   {'Year':<8} | {'Energy (MWh)':<14} | {'CO2 (t)':<10}")
        print("   " + "-" * 38)

        for m in c.environmental_metrics:
            print(f"""   {m.reporting_year:<8} |
                {m.energy_consumption_mwh:<14} | {m.carbon_emissions_tco2e:<10}""")

    print("\n" + "="*60)
    assert len(companies) > 0
    assert len(seed_metrics) > 0
