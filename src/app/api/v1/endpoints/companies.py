# src/app/api/v1/endpoints/companies.py
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.cache import (
    get_cached_object,
    invalidate_cache,
    set_cached_object,
)
from app.core.redis import get_redis_client
from app.database.session import get_db
from app.models.company import Company
from app.schemas.company_schema import (
    CompanyCreateRequest,
    CompanySchema,
    CompanyUpdate,
)
from app.schemas.loan_simulation_schema import (
    LoanSimulationCreate,
    LoanSimulationResponse,
)
from app.services.company_service import CompanyService
from app.services.loan_simulation_service import LoanSimulationService

router = APIRouter()

# Type aliases for clean dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
CacheClient = Annotated[Redis, Depends(get_redis_client)]


@router.post("/", response_model=CompanySchema, status_code=status.HTTP_201_CREATED)
async def create_company_endpoint(
    request: CompanyCreateRequest,
    db: DbSession,
    cache: CacheClient
):
    """Ingests a new company via the OpenCorporates API."""
    try:
        service = CompanyService(db=db, cache=cache)
        company = await service.register_company(request.company_number)
        return company
    except HTTPException as he:
        raise he from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/", response_model=list[CompanySchema])
async def list_companies(
    db: DbSession,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit")
) -> Sequence[Company]:
    """Retrieves a paginated list of all companies."""
    query = select(Company).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{company_id}", response_model=CompanySchema)
async def get_company(company_id: int, db: DbSession, cache: CacheClient):
    """Retrieves a specific company, utilizing Redis for high-performance reads."""
    cache_key = f"company:{company_id}"

    # 1. Try Redis Cache
    cached_company = await get_cached_object(cache, cache_key)
    if cached_company:
        return cached_company

    # 2. Fallback to Database
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalars().first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # 3. Populate Cache
    company_data = CompanySchema.model_validate(company).model_dump()
    await set_cached_object(cache, cache_key, company_data)

    return company_data


@router.patch("/{company_id}", response_model=CompanySchema)
async def update_company(
    company_id: int,
    company_in: CompanyUpdate,
    db: DbSession,
    cache: CacheClient
):
    """Updates a company and invalidates stale cache entries."""
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalars().first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Apply updates dynamically
    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)

    # Invalidate the cache to prevent stale data reads
    await invalidate_cache(cache, f"company:{company_id}")

    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: int, db: DbSession, cache: CacheClient):
    """Removes a company and purges its cache."""
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalars().first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    await db.delete(company)
    await db.commit()

    # Purge from cache
    await invalidate_cache(cache, f"company:{company_id}")


@router.post(
    "/{company_id}/simulate-loan",
    response_model=LoanSimulationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a Green Loan Simulation",
    description="Cross-references company data with regional emissions and \
        national energy datasets to calculate an ESG-adjusted interest rate."
)
async def simulate_green_loan(
    company_id: int,
    request: LoanSimulationCreate,
    db: DbSession
):
    """Calculates and persists a green loan simulation for a specific company."""
    try:
        service = LoanSimulationService(db=db)
        simulation = await service.generate_quote(
            company_id=company_id,
            loan_amount=request.loan_amount,
            term_months=request.term_months
        )
        return simulation
    except HTTPException as he:
        raise he from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {e!s}"
        ) from None
