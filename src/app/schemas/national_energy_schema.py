# src/app/schemas/national_energy_schema.py
"""
National Energy Pydantic Schemas.

This module defines the validation boundaries for reading national energy
reference data. It ensures that any data leaving the API adheres to expected
type constraints and formatting before it hits the network layer.
"""

from pydantic import BaseModel, ConfigDict, Field


class NationalEnergyBase(BaseModel):
    """
    Base Pydantic model for national energy metrics.

    Attributes:
        country (str): The nation the data applies to (max 255 chars).
        energy_type (str): The energy classification (max 100 chars).
        year (int): The 4-digit calendar year (constrained between 1900-2100).
        energy_consumption (float): Consumption value in Terawatt-hours (TWh).
        co2_emission (float): Emission value in Megatonnes of CO2 equivalent.
    """

    country: str = Field(..., max_length=255, examples=["United Kingdom"])
    energy_type: str = Field(..., max_length=100, examples=["Wind"])
    year: int = Field(..., ge=1900, le=2100)

    # Explicit descriptions ensure the auto-generated Swagger UI accurately
    # reflects the physical units of measurement used by the business logic.
    energy_consumption: float = Field(..., description="Energy consumption in TWh")
    co2_emission: float = Field(..., description="Emissions in MtCO2e")


class NationalEnergySchema(NationalEnergyBase):
    """
    Schema for serializing National Energy data into HTTP response payloads.

    Inherits all fields from NationalEnergyBase and appends the internal primary key.

    Attributes:
        id (int): The internal database ID.
    """

    id: int

    # Configures Pydantic to extract data directly from SQLAlchemy model attributes,
    # facilitating seamless ORM-to-JSON serialization.
    model_config = ConfigDict(from_attributes=True)
