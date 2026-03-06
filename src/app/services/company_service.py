# src/app/services/company_service.py
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company

from .opencorporates import OpenCorporatesClient


class CompanyService:
    def __init__(self, db: AsyncSession, cache: Redis):
        self.db = db
        self.cache = cache
        self.oc_client = OpenCorporatesClient()

    async def register_company(self, company_number: str) -> Company:
        # 1. Check if the company already exists in our database
        query = select(Company).where(
            Company.companies_house_id == company_number)
        result = await self.db.execute(query)
        existing_company = result.scalars().first()

        if existing_company:
            return existing_company

        # 2. Fetch raw data from OpenCorporates
        raw_data = await self.oc_client.get_company_details(company_number)

        # 3. Transform external data to match our schema
        sector = "Unknown"
        industry_codes = raw_data.get("industry_codes", [])
        if industry_codes:
            sector = industry_codes[0].get(
                "industry_code", {}).get("description", "Unknown")

        address_dict = raw_data.get("registered_address", {})
        location = address_dict.get("locality", "Unknown")

        # 4. Construct the entity and save to Postgres
        new_company = Company(
            companies_house_id=raw_data.get("company_number"),
            name=raw_data.get("name"),
            business_sector=sector,
            location=location,
            opencorporates_url=raw_data.get(
                "opencorporates_url")
        )

        self.db.add(new_company)
        await self.db.commit()
        await self.db.refresh(new_company)

        return new_company
