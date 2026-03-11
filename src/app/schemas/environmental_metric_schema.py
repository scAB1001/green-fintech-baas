# src/app/schemas/environmental_metric_schema.py
"""
Environmental Metric Pydantic Schemas.

This module defines the data validation boundaries for incoming and outgoing
ESG metric payloads. It utilizes Pydantic V2 numeric constraints to guarantee
that mathematically impossible values (e.g., negative carbon emissions) are
rejected at the API boundary before reaching the database.
"""

from pydantic import BaseModel, ConfigDict, Field


class EnvironmentalMetricBase(BaseModel):
    """
    Base Pydantic model containing shared ESG fields and the strict numeric constraints.

    Attributes:
        reporting_year (int): Must be a valid 4-digit year between 2000 and 2100.
        energy_consumption_mwh (float): Must be greater than or equal to zero.
        carbon_emissions_tco2e (float): Must be greater than or equal to zero.
        water_usage_m3 (float | None): Must be greater than or equal to zero.
        waste_generated_tonnes (float | None): Must be greater than or equal to zero.
    """

    # We use 'ge' (greater than or equal to) and 'le' (less than or equal to)
    # to enforce mathematical boundaries on the physical data.
    reporting_year: int = Field(..., ge=2000, le=2100, examples=[2025])
    energy_consumption_mwh: float = Field(..., ge=0, examples=[450.75])
    carbon_emissions_tco2e: float = Field(..., ge=0, examples=[12.5])
    water_usage_m3: float | None = Field(None, ge=0)
    waste_generated_tonnes: float | None = Field(None, ge=0)


class EnvironmentalMetricCreate(EnvironmentalMetricBase):
    """
    Schema for creating a new Environmental Metric.

    Inherits the strictly validated fields from the base schema and appends
    the required foreign key linking it to a specific corporate entity.

    Attributes:
        company_id (int): The primary key of the parent Company.
    """

    company_id: int


class EnvironmentalMetricUpdate(BaseModel):
    """
    Schema for partial updates (PATCH) to an existing Environmental Metric.

    All fields are intentionally optional to allow clients to update specific
    data points without needing to submit the entire yearly payload again.
    The numeric constraints remain strictly enforced on any provided fields.

    Attributes:
        reporting_year (int | None): Updated 4-digit year.
        energy_consumption_mwh (float | None): Updated energy usage.
        carbon_emissions_tco2e (float | None): Updated carbon emissions.
        water_usage_m3 (float | None): Updated water usage.
        waste_generated_tonnes (float | None): Updated waste generation.
    """

    reporting_year: int | None = Field(None, ge=2000, le=2100)
    energy_consumption_mwh: float | None = Field(None, ge=0)
    carbon_emissions_tco2e: float | None = Field(None, ge=0)
    water_usage_m3: float | None = Field(None, ge=0)
    waste_generated_tonnes: float | None = Field(None, ge=0)


class EnvironmentalMetricSchema(EnvironmentalMetricBase):
    """
    Schema for serializing Environmental Metric data into HTTP response payloads.

    Inherits all validated fields from EnvironmentalMetricBase and appends
    the internal primary and foreign keys. It is explicitly configured to
    read data directly from SQLAlchemy ORM models.

    Attributes:
        id (int): The internal PostgreSQL primary key.
        company_id (int): The foreign key linking to the parent Company.
    """

    id: int
    company_id: int

    # Allows Pydantic to serialize SQLAlchemy ORM instances into JSON
    model_config = ConfigDict(from_attributes=True)
