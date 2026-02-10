# src/app/api/v1/endpoints/companies.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.company import Company

router = APIRouter()


@router.get("/", response_model=list[dict])
async def read_companies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve list of companies."""
    result = await db.execute(select(Company).offset(skip).limit(limit))
    companies = result.scalars().all()
    return [
        {
            "id": company.id,
            "companies_house_id": company.companies_house_id,
            "name": company.name,
            "business_sector": company.business_sector,
            "location": company.location,
        }
        for company in companies
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Create a new company."""
    try:
        company = Company(**company_data)
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return {
            "id": company.id,
            "message": "Company created successfully",
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating company: {str(e)}",
        )


@router.get("/{company_id}")
async def read_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a specific company by ID."""
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return {
        "id": company.id,
        "companies_house_id": company.companies_house_id,
        "name": company.name,
        "business_sector": company.business_sector,
        "location": company.location,
    }
