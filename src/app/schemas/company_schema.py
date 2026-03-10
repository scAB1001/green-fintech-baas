# src/app/schemas/company_schema.py
"""
Company Pydantic Schemas.



This module defines the data validation boundaries for the Company domain.
It utilizes Pydantic V2 to enforce strict type checking, string constraints,
and OpenAPI schema generation before any data reaches the FastAPI routers
or the SQLAlchemy ORM layer.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Reusable type alias for Companies House ID validation.
# Enforces a strict 8-character limit as mandated by the UK government registry,
# failing fast if a client provides a malformed identifier.
CH_ID = Annotated[str, StringConstraints(min_length=8, max_length=8)]


class CompanyBase(BaseModel):
    """
    Base Pydantic model containing fields shared across all Company schemas.

    Attributes:
        name (str): The legal name of the corporate entity.
        companies_house_id (CH_ID): The strictly validated 8-character registry ID.
        business_sector (str | None): The industry classification (e.g., Energy).
        location (str | None): The primary UK regional local authority.
        opencorporates_url (str | None): A direct link to the registry profile.
    """

    name: str = Field(
        ..., min_length=1, max_length=255, examples=["EcoTech Manufacturing Ltd"]
    )
    companies_house_id: CH_ID = Field(..., examples=["12345678"])
    business_sector: str | None = Field(
        None, max_length=100, examples=["Energy"])
    location: str | None = Field(None, max_length=100, examples=["Birmingham"])
    opencorporates_url: str | None = Field(
        None, description="Mandatory attribution link"
    )


class CompanyCreateRequest(BaseModel):
    """
    Schema specifically for the OpenCorporates ingestion endpoint payload.

    Instead of requiring the client to provide all company details, the client
    only submits the registration number, and the BaaS fetches the remainder
    from the external OpenCorporates API.

    Attributes:
        company_number (CH_ID): The strictly validated 8-character ID.
    """

    company_number: CH_ID = Field(
        ..., description="The 8-character Companies House ID"
    )


class CompanyUpdate(BaseModel):
    """
    Schema for partial updates (PATCH) to an existing company.

    All fields are intentionally optional to allow clients to update only
    specific attributes without needing to send the entire resource payload.

    Attributes:
        name (str | None): The updated company name.
        business_sector (str | None): The updated industry classification.
        location (str | None): The updated UK regional location.
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    business_sector: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)


class CompanySchema(CompanyBase):
    """
    Schema for serializing Company data into HTTP response payloads.

    Inherits all fields from CompanyBase and appends the internal primary key.
    It is explicitly configured to read data directly from SQLAlchemy ORM models.

    Attributes:
        id (int): The internal PostgreSQL primary key.
    """

    id: int

    # ConfigDict(from_attributes=True) replaces deprecated class Config: orm_mode=True
    # It allows Pydantic to read data as `obj.name` instead of just `obj['name']`,
    # which is strictly required for serializing SQLAlchemy ORM instances into JSON.
    model_config = ConfigDict(from_attributes=True)
