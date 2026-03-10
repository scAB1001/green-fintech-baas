# src/app/schemas/national_energy_schema.py
from pydantic import BaseModel, ConfigDict, Field


class NationalEnergyBase(BaseModel):
    country: str = Field(..., max_length=255, examples=["United Kingdom"])
    energy_type: str = Field(..., max_length=100, examples=["Wind"])
    year: int = Field(..., ge=1900, le=2100)
    energy_consumption: float = Field(..., description="Energy consumption in TWh")
    co2_emission: float = Field(..., description="Emissions in MtCO2e")


class NationalEnergySchema(NationalEnergyBase):
    """Response schema for National Energy data."""

    id: int

    model_config = ConfigDict(from_attributes=True)
