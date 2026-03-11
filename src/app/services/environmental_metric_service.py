# src/app/services/environmental_metric_service.py
"""
Environmental Metric Service Layer.

Handles the ingestion and management of actual company ESG data. This service
ensures referential integrity and enforces the business rule that a company
can only submit one set of environmental metrics per fiscal/reporting year.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.company import Company
from app.models.environmental_metric import EnvironmentalMetric
from app.schemas.environmental_metric_schema import (
    EnvironmentalMetricBase,
)


class EnvironmentalMetricService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_metric(
        self, company_id: int, metric_in: EnvironmentalMetricBase
    ) -> EnvironmentalMetric:
        """
        Validates the parent company and persists a new yearly metric record.
        """
        # 1. Verify the parent company exists
        company = await self.db.get(Company, company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
            )

        # 2. Enforce the unique year constraint gracefully
        query = select(EnvironmentalMetric).where(
            EnvironmentalMetric.company_id == company_id,
            EnvironmentalMetric.reporting_year == metric_in.reporting_year,
        )
        result = await self.db.execute(query)
        if result.scalars().first():
            logger.warning(
                f"Duplicate metric submission for company {company_id}, "
                f"year {metric_in.reporting_year}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Metrics for year {metric_in.reporting_year} already exist.",
            )

        # 3. Construct and persist
        new_metric = EnvironmentalMetric(
            company_id=company_id,
            **metric_in.model_dump()
        )

        self.db.add(new_metric)
        await self.db.commit()
        await self.db.refresh(new_metric)

        logger.info(
            f"Successfully added {metric_in.reporting_year} metrics "
            f"for company {company_id}"
        )
        return new_metric

    async def get_company_metrics(self, company_id: int) -> list[EnvironmentalMetric]:
        """
        Retrieves all historical metrics for a company, ordered by year.
        """
        query = (
            select(EnvironmentalMetric)
            .where(EnvironmentalMetric.company_id == company_id)
            .order_by(EnvironmentalMetric.reporting_year.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
