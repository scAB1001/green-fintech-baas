# src/app/schemas/loan_simulation_schema.py
"""
Loan Simulation Pydantic Schemas.

This module defines the validation boundaries for the loan simulation engine.
It enforces strict mathematical constraints on incoming loan requests
(e.g., maximum term limits) and serializes the complex ESG interest rate
calculations into standardized JSON responses.
"""

from pydantic import BaseModel, ConfigDict, Field


# TODO: Extend currency support for non-GBP loans in future iterations.
class LoanSimulationBase(BaseModel):
    """
    Base Pydantic model defining the core inputs for a loan quote.

    Attributes:
        loan_amount (float): Must be greater than 0. Currently assumes GBP.
        term_months (int): Must be between 1 and 360 months (30 years).
    """

    loan_amount: float = Field(
        ..., gt=0, description="The requested loan amount in GBP", examples=[500000.0]
    )
    term_months: int = Field(
        ...,
        gt=0,
        le=360,  # Hard limit to prevent integer overflow in amortization math
        description="The loan term in months (max 30 years)",
        examples=[60],
    )


class LoanSimulationCreate(LoanSimulationBase):
    """
    Schema for requesting a new green loan simulation via the API.

    Inherits all constraints from LoanSimulationBase. It is isolated as an
    empty subclass to allow for future request-specific fields (like regional
    overrides) without polluting the base model used for responses.
    """

    pass


class LoanSimulationResponse(LoanSimulationBase):
    """
    Schema for serializing the completed loan simulation into an HTTP response.

    Combines the original request parameters with the server-calculated
    Environmental Performance Score (EPS) and the resulting margin ratchet
    (discounted interest rate).

    Attributes:
        id (int): The database primary key.
        company_id (int): The ID of the corporate entity receiving the quote.
        base_rate (float): The standard market rate before ESG discounts.
        applied_rate (float): The final, discounted rate.
        esg_score (float): The calculated EPS (0-100 scale).
        estimated_carbon_savings (float): Projected tonnes of CO2 saved.
    """

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

    # Instructs Pydantic to read directly from the SQLAlchemy LoanSimulation model
    model_config = ConfigDict(from_attributes=True)
