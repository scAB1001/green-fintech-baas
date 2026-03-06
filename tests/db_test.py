# tests/db_test.py
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

    # 1. Fetch Companies with EnvironmentalMetrics eagerly loaded
    # Prevents the "MissingGreenlet" error when accessing c.environmental_metrics
    stmt = select(Company).options(selectinload(Company.environmental_metrics))
    result = await db_session.execute(stmt)
    companies = result.scalars().all()

    assert len(companies) > 0
    assert len(seed_metrics) > 0
