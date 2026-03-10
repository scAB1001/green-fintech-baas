# src/app/schemas/regional_emission_schema.py
"""
Regional Emission Pydantic Schemas.

This module provides the validation layer for regional ESG data. It ensures
that data imported from CSVs or external government APIs meets the strict
type requirements before being utilized in financial calculations.
"""

from pydantic import BaseModel, ConfigDict, Field


class RegionalEmissionBase(BaseModel):
    """
    Base Pydantic model for regional emission data.

    Attributes:
        local_authority (str): The UK local authority name.
        year (int): The year the data represents (1900-2100).
        industry_total (float): Defaults to 0.0 if data is missing for the sector.
        grand_total (float): The sum of all sectoral emissions.
    """

    local_authority: str = Field(..., max_length=255, examples=["Leeds"])
    year: int = Field(..., ge=1900, le=2100)

    # Sectoral breakdowns are initialized with defaults to accommodate
    # datasets with partial information or missing columns.
    industry_total: float = Field(default=0.0)
    commercial_total: float = Field(default=0.0)
    public_sector_total: float = Field(default=0.0)
    domestic_total: float = Field(default=0.0)
    transport_total: float = Field(default=0.0)
    agriculture_total: float = Field(default=0.0)
    grand_total: float = Field(default=0.0)


class RegionalEmissionSchema(RegionalEmissionBase):
    """
    Response schema for Regional Emission data.

    Includes the internal ID for resource identification.
    Configured to support SQLAlchemy ORM mapping.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
