# src/app/schemas/loan_simulation_schema.py
from pydantic import BaseModel, ConfigDict, Field


# TODO: For non-GBP also
class LoanSimulationBase(BaseModel):
    """Base fields for a green loan simulation."""

    loan_amount: float = Field(
        ..., gt=0, description="The requested loan amount in GBP", examples=[500000.0]
    )
    term_months: int = Field(
        ...,
        gt=0,
        le=360,
        description="The loan term in months (max 30 years)",
        examples=[60],
    )


class LoanSimulationCreate(LoanSimulationBase):
    """Schema for requesting a new loan simulation."""

    pass


class LoanSimulationResponse(LoanSimulationBase):
    """Schema for returning the calculated loan simulation data."""

    id: int
    company_id: int
    base_rate: float = Field(..., description="The standard market interest rate (%)")
    applied_rate: float = Field(
        ..., description="The discounted interest rate applied post ESG assessment (%)"
    )
    esg_score: float = Field(
        ..., description="The calculated Environmental Performance Score (0-100)"
    )
    estimated_carbon_savings: float = Field(
        ..., description="Projected CO2 savings (tonnes) linked to the loan usage"
    )

    model_config = ConfigDict(from_attributes=True)
