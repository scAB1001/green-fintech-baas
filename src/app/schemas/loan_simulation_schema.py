from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoanSimulationBase(BaseModel):
    loan_amount_gbp: float = Field(..., gt=0, examples=[500000.00])
    loan_term_years: int = Field(..., gt=0, le=30, examples=[5])
    base_interest_rate: float = Field(..., ge=0, le=1, examples=[0.045])


class LoanSimulationCreate(LoanSimulationBase):
    company_id: int


class LoanSimulationSchema(LoanSimulationBase):
    id: UUID
    company_id: int
    green_score: float
    green_discount: float
    simulated_final_rate: float
    estimated_co2_savings_tco2e: float | None
    created_at: datetime
    simulation_parameters: str | None

    model_config = ConfigDict(from_attributes=True)
