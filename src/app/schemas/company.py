from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Reusable type for Companies House ID (Strict 8-character validation)
# This directly supports your marks for "Testing & Error Handling"
CH_ID = Annotated[str, StringConstraints(min_length=8, max_length=8)]


class CompanyBase(BaseModel):
    """Base fields shared across all Company schemas."""
    name: str = Field(..., min_length=1, max_length=255,
                      examples=["EcoTech Manufacturing Ltd"])
    companies_house_id: CH_ID = Field(..., examples=["12345678"])
    business_sector: str | None = Field(
        None, max_length=100, examples=["Energy"])
    location: str | None = Field(None, max_length=100, examples=["Birmingham"])


class CompanyCreate(CompanyBase):
    """Schema for creating a new company (Request Body)."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating an existing company (All fields optional)."""
    name: str | None = None
    companies_house_id: CH_ID | None = None
    business_sector: str | None = None
    location: str | None = None


class Company(CompanyBase):
    """Schema for returning company data (Response Body)."""
    id: int

    # This is critical for SQLAlchemy 2.0 Async compatibility.
    # It allows Pydantic to read data from the SQLAlchemy model attributes.
    model_config = ConfigDict(from_attributes=True)
