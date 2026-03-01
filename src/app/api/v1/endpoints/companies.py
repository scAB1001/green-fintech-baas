# src/app/api/v1/endpoints/companies.py
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.cache import get_cached_object, set_cached_object
from app.database.session import get_db
from app.models.company import Company
from app.schemas.company_schema import CompanySchema

router = APIRouter()

# 1. Define the dependency using Annotated to avoid E:B008
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/{company_id}", response_model=CompanySchema)
async def get_company(company_id: int, db: DbSession):
    cache_key = f"company:{company_id}"

    # 2. Try to get from Redis
    cached_company = await get_cached_object(cache_key)
    if cached_company:
        return cached_company  # Return immediately

    # 3. If not in Redis, get from Postgres (using async select)
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalars().first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # 4. Convert SQLAlchemy model to Pydantic dict and save to Redis
    company_data = CompanySchema.model_validate(company).model_dump()
    await set_cached_object(cache_key, company_data)

    return company_data
