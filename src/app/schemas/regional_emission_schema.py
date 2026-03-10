# src/app/schemas/regional_emission_schema.py
from pydantic import BaseModel, ConfigDict, Field


class RegionalEmissionBase(BaseModel):
    local_authority: str = Field(..., max_length=255, examples=["Leeds"])
    year: int = Field(..., ge=1900, le=2100)
    industry_total: float = Field(default=0.0)
    commercial_total: float = Field(default=0.0)
    public_sector_total: float = Field(default=0.0)
    domestic_total: float = Field(default=0.0)
    transport_total: float = Field(default=0.0)
    agriculture_total: float = Field(default=0.0)
    grand_total: float = Field(default=0.0)


class RegionalEmissionSchema(RegionalEmissionBase):
    """Response schema for Regional Emission data."""

    id: int

    model_config = ConfigDict(from_attributes=True)
