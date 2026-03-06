# src/app/schemas/company_schema.py
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Reusable type for Companies House ID (Strict 8-character validation)
CH_ID = Annotated[str, StringConstraints(min_length=8, max_length=8)]


class CompanyBase(BaseModel):
    """Base fields shared across all Company schemas."""
    name: str = Field(..., min_length=1, max_length=255,
                      examples=["EcoTech Manufacturing Ltd"])
    companies_house_id: CH_ID = Field(..., examples=["12345678"])
    business_sector: str | None = Field(
        None, max_length=100, examples=["Energy"])
    location: str | None = Field(None, max_length=100, examples=["Birmingham"])
    opencorporates_url: str | None = Field(
        None, description="Mandatory attribution link")


class CompanyCreateRequest(BaseModel):
    """Schema specifically for the OpenCorporates ingestion endpoint."""
    company_number: CH_ID = Field(...,
                                  description="The 8-character Companies House ID")


class CompanyUpdate(BaseModel):
    """Schema for updating an existing company (All fields optional)."""
    name: str | None = Field(None, min_length=1, max_length=255)
    business_sector: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)


class CompanySchema(CompanyBase):
    """Schema for returning company data (Response Body)."""
    id: int

    model_config = ConfigDict(from_attributes=True)
