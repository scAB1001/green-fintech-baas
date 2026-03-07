# src/app/services/company_service.py
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.company import Company

from .opencorporates import OpenCorporatesClient


class CompanyService:
    def __init__(self, db: AsyncSession, cache: Redis):
        self.db = db
        self.cache = cache
        self.oc_client = OpenCorporatesClient()

    async def register_company(self, company_number: str) -> Company:
        logger.info(f"Initiating registration for company number: {company_number}")
        # 1. Check if the company already exists in our database
        query = select(Company).where(Company.companies_house_id == company_number)
        result = await self.db.execute(query)
        existing_company = result.scalars().first()

        if existing_company:
            logger.info(f"Company {company_number} found in local database. \
                    Skipping external API call.")
            return existing_company

        # 2. Fetch raw data from OpenCorporates
        logger.debug(f"Company {company_number} not found locally. \
                Fetching from OpenCorporates.")
        raw_data = await self.oc_client.get_company_details(company_number)

        # 3. Transform external data to match our schema safely
        sector = "Unknown"
        # Use 'or []' in case industry_codes is explicitly None
        industry_codes = raw_data.get("industry_codes") or []
        if industry_codes:
            # Safely navigate the nested dicts and fallback if description is None
            industry_code_dict = industry_codes[0].get("industry_code") or {}
            sector = industry_code_dict.get("description") or "Unknown"

        # Use 'or {}' in case registered_address is explicitly None
        address_dict = raw_data.get("registered_address") or {}
        # Use 'or "Unknown"' to catch explicit None values inside the locality field
        location = address_dict.get("locality") or "Unknown"

        logger.debug(f"Transformed data for {company_number}: Sector='{sector}', \
                Location='{location}'")

        # 4. Construct the entity and save to Postgres
        new_company = Company(
            companies_house_id=raw_data.get("company_number"),
            name=raw_data.get("name"),
            business_sector=sector,
            location=location,
            opencorporates_url=raw_data.get("opencorporates_url"),
        )

        self.db.add(new_company)
        await self.db.commit()
        await self.db.refresh(new_company)

        logger.info(f"Successfully registered new company: '{new_company.name}' \
                (ID: {new_company.id})")

        return new_company
