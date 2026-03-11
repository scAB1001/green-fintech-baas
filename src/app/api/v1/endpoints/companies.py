# src/app/api/v1/endpoints/companies.py
"""
Company and Loan Simulation Endpoints.



This module defines the primary HTTP routing layer for the `Company` domain.
It handles corporate data ingestion, ESG loan simulations, bulk CSV exports,
and dynamic PDF generation. It aggressively utilizes the Redis caching layer
via the Cache-Aside pattern to minimize database I/O and latency.
"""

import base64
import csv
import io
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.cache import (
    get_cached_object,
    invalidate_cache,
    invalidate_pattern,
    set_cached_object,
)
from app.core.redis import get_redis_client
from app.database.session import get_db
from app.models.company import Company
from app.models.loan_simulation import LoanSimulation
from app.schemas.company_schema import (
    CompanyCreateRequest,
    CompanySchema,
    CompanyUpdate,
)
from app.schemas.environmental_metric_schema import (
    EnvironmentalMetricBase,
    EnvironmentalMetricSchema,
)
from app.schemas.loan_simulation_schema import (
    LoanSimulationCreate,
    LoanSimulationResponse,
)
from app.services.company_service import CompanyService
from app.services.environmental_metric_service import EnvironmentalMetricService
from app.services.loan_simulation_service import LoanSimulationService
from app.services.pdf_service import PDFService

router = APIRouter()

# Type aliases for clean dependency injection across route signatures
DbSession = Annotated[AsyncSession, Depends(get_db)]
CacheClient = Annotated[Redis, Depends(get_redis_client)]


@router.post("/", response_model=CompanySchema, status_code=status.HTTP_201_CREATED)
async def create_company_endpoint(
    request: CompanyCreateRequest, db: DbSession, cache: CacheClient
) -> Company | None:
    """
    Ingests a new company via the OpenCorporates API.

    Delegates the external API orchestration to the CompanyService. Upon
    successful persistence, it aggressively invalidates relevant cache keys
    to prevent stale paginated lists or outdated CSV exports.

    Args:
        request (CompanyCreateRequest): The JSON payload containing the registry ID.
        db (DbSession): The active database session.
        cache (CacheClient): The active Redis client.

    Returns:
        Company | None: The newly persisted SQLAlchemy entity.

    Raises:
        HTTPException: If the external API fails or data is invalid.
    """
    try:
        service = CompanyService(db=db, cache=cache)
        company = await service.register_company(request.company_number)

        # INVALIDATE: A new company alters lists and CSVs
        await invalidate_pattern(cache, "companies:list:*")
        await invalidate_cache(cache, "companies:csv")

        return company
    except HTTPException as he:
        raise he from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get("/", response_model=list[CompanySchema])
async def list_companies(
    db: DbSession,
    cache: CacheClient,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
) -> dict[str, str] | list[dict[str, Any]]:
    """
    Retrieves a paginated list of all companies.

    Utilizes the Cache-Aside pattern. The cache key includes pagination
    parameters to ensure deterministic caching per page view.

    Args:
        db (DbSession): The active database session.
        cache (CacheClient): The active Redis client.
        skip (int): The number of records to skip (offset).
        limit (int): The maximum number of records to return.

    Returns:
        list[dict[str, Any]]: A list of serialized Company dictionaries.
    """
    cache_key = f"companies:list:{skip}:{limit}"

    # 1. Try Cache
    cached_list = await get_cached_object(cache, cache_key)
    if cached_list:
        return cached_list

    # 2. Database Fallback
    query = select(Company).offset(skip).limit(limit)
    result = await db.execute(query)
    companies = result.scalars().all()

    # 3. Populate Cache (60s TTL for lists to balance data freshness and performance)
    companies_data = [CompanySchema.model_validate(c).model_dump() for c in companies]
    await set_cached_object(cache, cache_key, companies_data, expire=60)

    return companies_data


@router.get("/{company_id}", response_model=CompanySchema)
async def get_company(
    company_id: int, db: DbSession, cache: CacheClient
) -> dict[str, Any]:
    """
    Retrieves a specific company by its internal ID.

    Utilizes Redis for high-performance reads on frequently accessed entities.

    Args:
        company_id (int): The internal primary key of the company.
        db (DbSession): The active database session.
        cache (CacheClient): The active Redis client.

    Returns:
        dict[str, Any]: The serialized Company dictionary.

    Raises:
        HTTPException: 404 if the company does not exist in the database.
    """
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    # 3. Populate Cache
    company_data = CompanySchema.model_validate(company).model_dump()
    await set_cached_object(cache, cache_key, company_data)

    return company_data


@router.patch("/{company_id}", response_model=CompanySchema)
async def update_company(
    company_id: int, company_in: CompanyUpdate, db: DbSession, cache: CacheClient
) -> Company:
    """
    Updates specific attributes of an existing corporate entity.

    Applies partial updates to the database and proactively invalidates
    all related cache keys to prevent data drift across the platform.

    Args:
        company_id (int): The unique identifier of the company.
        company_in (CompanyUpdate): The payload containing updated fields.
        db (DbSession): The active database session.
        cache (CacheClient): The active Redis client.

    Returns:
        Company: The updated SQLAlchemy model instance.

    Raises:
        HTTPException: 404 if the company does not exist.
    """
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalars().first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    # Only extract fields that were explicitly set in the request payload
    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)

    # INVALIDATE: Clear entity, paginated lists, and CSV dumps
    await invalidate_cache(cache, f"company:{company_id}")
    await invalidate_pattern(cache, "companies:list:*")
    await invalidate_cache(cache, "companies:csv")

    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: int, db: DbSession, cache: CacheClient) -> None:
    """
    Hard-deletes a company and cascades deletions to related records.

    Args:
        company_id (int): The unique identifier of the company.
        db (DbSession): The active database session.
        cache (CacheClient): The active Redis client.

    Raises:
        HTTPException: 404 if the company does not exist.
    """
    query = select(Company).where(Company.id == company_id)
    result = await db.execute(query)
    company = result.scalars().first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    await db.delete(company)
    await db.commit()

    # INVALIDATE: Clear entity, paginated lists, and CSV dumps
    await invalidate_cache(cache, f"company:{company_id}")
    await invalidate_pattern(cache, "companies:list:*")
    await invalidate_cache(cache, "companies:csv")


@router.post(
    "/{company_id}/simulate-loan",
    response_model=LoanSimulationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a Green Loan Simulation",
    description="Cross-references company data with regional emissions and \
        national energy datasets to calculate an ESG-adjusted interest rate.",
)
async def simulate_green_loan(
    company_id: int, request: LoanSimulationCreate, db: DbSession
) -> LoanSimulation | None:
    """
    Calculates and persists a dynamic green loan simulation.

    Executes the core ESG mathematical engine via the LoanSimulationService.
    This endpoint mutates state and is intentionally excluded from caching.

    Args:
        company_id (int): The unique identifier of the target company.
        request (LoanSimulationCreate): The loan parameters (amount, term).
        db (DbSession): The active database session.

    Returns:
        LoanSimulation | None: The persisted simulation results.

    Raises:
        HTTPException: 500 if the underlying mathematical simulation fails.
    """
    try:
        service = LoanSimulationService(db=db)
        return await service.generate_quote(
            company_id=company_id,
            loan_amount=request.loan_amount,
            term_months=request.term_months,
        )
    except HTTPException as he:
        raise he from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {e!s}",
        ) from None


@router.get(
    "/export/csv",
    summary="Export Companies to CSV",
    response_class=Response,
    response_model=None,
    responses={
        200: {
            "content": {"text/csv": {}},
            "description": "A CSV export of all registered companies.",
        }
    },
)
async def export_companies_csv(db: DbSession, cache: CacheClient) -> Response:
    """
    Generates a bulk CSV export of all corporate entities.

    Because CSV generation is computationally expensive at scale, the raw string
    output is heavily cached in Redis.

    Args:
        db (DbSession): The active database session.
        cache (CacheClient): The active Redis client.

    Returns:
        Response: A raw HTTP response with text/csv media type and attachment headers.
    """
    cache_key = "companies:csv"

    # 1. Try Cache (CSV is just a string, so we read it directly from Redis)
    cached_csv = await cache.get(cache_key)
    if cached_csv:
        return Response(
            content=cached_csv,
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="companies_export.csv"'
            },
        )

    # 2. Database Fallback
    query = select(Company)
    result = await db.execute(query)
    companies = result.scalars().all()

    # Utilize an in-memory string buffer to construct the CSV payload
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Company Number", "Name", "Sector", "Location"])
    for c in companies:
        writer.writerow(
            [c.id, c.companies_house_id, c.name, c.business_sector, c.location]
        )

    csv_data = output.getvalue()

    # 3. Populate Cache
    await cache.setex(cache_key, 3600, csv_data)

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="companies_export.csv"'},
    )


@router.get(
    "/{company_id}/simulate-loan/{simulation_id}/pdf",
    summary="Download Loan Simulation PDF",
    response_class=Response,
    response_model=None,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "The rendered PDF document.",
        }
    },
)
async def get_loan_simulation_pdf(
    company_id: int, simulation_id: int, db: DbSession, cache: CacheClient
) -> None | Response:
    """
    Generates a dynamic PDF formal quote for a loan simulation.

    PDF generation blocks the event loop. To optimize, the binary output is
    encoded to Base64 (because Redis is configured with decode_responses=True)
    and cached extensively.

    Args:
        company_id (int): The unique identifier of the company.
        simulation_id (int): The unique identifier of the loan simulation.
        db (DbSession): The active database session.
        cache (CacheClient): The active Redis client.

    Returns:
        Response: A raw HTTP response with application/pdf media type.

    Raises:
        HTTPException: 404 if the company or simulation cannot be found.
    """
    cache_key = f"simulation:{simulation_id}:pdf"

    # 1. Try Cache
    # Since the Redis client decodes responses to UTF-8 strings automatically,
    # we must base64 decode the stored string back into binary bytes for the PDF.
    cached_pdf_b64 = await cache.get(cache_key)
    if cached_pdf_b64:
        pdf_bytes = base64.b64decode(cached_pdf_b64)
        pre = "green_loan_quote_"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{pre}{company_id}.pdf"'
            },
        )

    # 2. Database Fallback
    company_query = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_query)
    company = company_result.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    sim_query = select(LoanSimulation).where(LoanSimulation.id == simulation_id)
    sim_result = await db.execute(sim_query)
    simulation = sim_result.scalars().first()

    if not simulation or simulation.company_id != company_id:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Generate the binary PDF payload
    pdf_bytes = PDFService.generate_loan_quote_pdf(company, simulation)

    # 3. Populate Cache
    # Encode binary bytes to a base64 UTF-8 string so Redis can store it safely
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    await cache.setex(cache_key, 86400, b64_pdf)  # Cache for 24 hours

    pre = "green_loan_quote_"
    house_id = company.companies_house_id
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pre}{house_id}.pdf"'},
    )


@router.post(
    "/{company_id}/metrics",
    response_model=EnvironmentalMetricSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add Yearly ESG Metrics",
)
async def add_company_metrics(
    company_id: int, request: EnvironmentalMetricBase, db: DbSession, cache: CacheClient
) -> EnvironmentalMetricSchema:
    """
    Submits actual yearly environmental performance data for a company.

    This data is stored to be utilized by the loan simulation engine for
    calculating accurate Margin Ratchets.
    """
    try:
        service = EnvironmentalMetricService(db=db)
        metric = await service.add_metric(company_id=company_id, metric_in=request)

        # INVALIDATE: Clear the company's cached metric list
        await invalidate_cache(cache, f"company:{company_id}:metrics")

        return metric
    except HTTPException as he:
        raise he from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


@router.get(
    "/{company_id}/metrics",
    response_model=list[EnvironmentalMetricSchema],
    summary="List Company ESG Metrics",
)
async def list_company_metrics(
    company_id: int, db: DbSession, cache: CacheClient
) -> dict[str, str] | list[dict[str, Any]]:
    """
    Retrieves the historical ESG performance data for a specific company.
    """
    cache_key = f"company:{company_id}:metrics"

    # 1. Try Cache
    cached_metrics = await get_cached_object(cache, cache_key)
    if cached_metrics:
        return cached_metrics

    # 2. Database Fallback
    service = EnvironmentalMetricService(db=db)
    metrics = await service.get_company_metrics(company_id)

    # 3. Populate Cache
    metrics_data = [
        EnvironmentalMetricSchema.model_validate(m).model_dump() for m in metrics
    ]
    await set_cached_object(cache, cache_key, metrics_data)

    return metrics_data
