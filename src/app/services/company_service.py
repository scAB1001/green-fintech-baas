# src/app/services/company_service.py
"""
Company Service Layer.



This module implements the core business logic for company management,
specifically the "Upsert-from-External" pattern. It acts as the orchestrator
between our local persistence (PostgreSQL/SQLAlchemy), the distributed cache
(Redis), and the external OpenCorporates registry.
"""

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.company import Company

from .opencorporates_service import OpenCorporatesClient


class CompanyService:
    """
    Service handle for Company-related business operations.

    Args:
        db (AsyncSession): The SQLAlchemy asynchronous session for database IO.
        cache (Redis): Redis client for caching operations (reserved for future use).
    """

    def __init__(self, db: AsyncSession, cache: Redis):
        self.db = db
        self.cache = cache
        self.oc_client = OpenCorporatesClient()

    async def register_company(self, company_number: str) -> Company:
        """
        Registers a company by its UK Companies House ID.

        Logic Flow:
        1. Idempotency Check: Verify if the entity already exists in our DB.
        2. External Fetch:
            If not found, retrieve verified legal data from OpenCorporates.
        3. Data Normalization: Map nested third-party JSON to our internal Domain Model.
        4. Persistence: Commit the new record to PostgreSQL.

        Args:
            company_number (str): The 8-character UK registration number.

        Returns:
            Company: The persisted SQLAlchemy ORM instance.

        Raises:
            HTTPException: Propagated from oc_client if company is not found globally.
        """
        logger.info(
            f"Initiating registration for company number: {company_number}")

        # 1. Idempotency Check
        # We perform a primary lookup on the unique Companies House ID to prevent
        # duplicate entries and unnecessary external API billing.
        query = select(Company).where(
            Company.companies_house_id == company_number)
        result = await self.db.execute(query)
        existing_company = result.scalars().first()

        if existing_company:
            logger.info(f"Company {company_number} found in local database. "
                        "Skipping external API call.")
            return existing_company

        # 2. External Data Fetch
        logger.debug(f"Company {company_number} not found locally. "
                     "Fetching from OpenCorporates.")
        raw_data = await self.oc_client.get_company_details(company_number)

        # 3. Defensive Data Transformation
        # OpenCorporates data structures can vary by jurisdiction. We use defensive
        # programming with fallbacks to ensure the service layer doesn't crash on
        # missing nested fields.

        # Extract Business Sector (Industry Classification)
        sector = "Unknown"
        industry_codes = raw_data.get("industry_codes") or []
        if industry_codes:
            industry_code_dict = industry_codes[0].get("industry_code") or {}
            sector = industry_code_dict.get("description") or "Unknown"

        # Extract Geographic Location
        address_dict = raw_data.get("registered_address") or {}
        location = address_dict.get("locality") or "Unknown"

        logger.debug(f"Transformed data for {company_number}: Sector='{sector}', "
                     f"Location='{location}'")

        # 4. Persistence
        # Constructing the Entity using the normalized data.
        new_company = Company(
            companies_house_id=raw_data.get("company_number"),
            name=raw_data.get("name"),
            business_sector=sector,
            location=location,
            opencorporates_url=raw_data.get("opencorporates_url"),
        )

        self.db.add(new_company)
        await self.db.commit()
        # Refresh to load the DB-generated PK (ID)
        await self.db.refresh(new_company)

        logger.info(f"Successfully registered new company: '{new_company.name}' "
                    f"(ID: {new_company.id})")

        return new_company
