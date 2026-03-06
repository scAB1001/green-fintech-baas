# src/app/schemas/environmental_metric_schema.py
from pydantic import BaseModel, ConfigDict, Field


class EnvironmentalMetricBase(BaseModel):
    reporting_year: int = Field(..., ge=2000, le=2100, examples=[2025])
    energy_consumption_mwh: float = Field(..., ge=0, examples=[450.75])
    carbon_emissions_tco2e: float = Field(..., ge=0, examples=[12.5])
    water_usage_m3: float | None = Field(None, ge=0)
    waste_generated_tonnes: float | None = Field(None, ge=0)


class EnvironmentalMetricCreate(EnvironmentalMetricBase):
    company_id: int


class EnvironmentalMetricSchema(EnvironmentalMetricBase):
    id: int
    company_id: int

    model_config = ConfigDict(from_attributes=True)
