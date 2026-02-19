import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

from . import Company  # Import the Company model for the relationship


class LoanSimulation(Base):
    __tablename__ = "loan_simulations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, index=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"))

    # Loan parameters
    loan_amount_gbp: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False)
    loan_term_years: Mapped[int] = mapped_column(nullable=False)
    base_interest_rate: Mapped[float] = mapped_column(
        Numeric(4, 3), nullable=False)  # e.g., 0.045

    # Green adjustments
    green_score: Mapped[float] = mapped_column(Numeric(5, 2))  # e.g., 82.50
    green_discount: Mapped[float] = mapped_column(Numeric(4, 3))  # e.g., 0.005
    simulated_final_rate: Mapped[float] = mapped_column(
        Numeric(4, 3), nullable=False)

    # Impact metrics
    estimated_co2_savings_tco2e: Mapped[float |
                                        None] = mapped_column(Numeric(10, 2))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    simulation_parameters: Mapped[str | None] = mapped_column(
        String)  # Could store JSON

    # Relationship
    company: Mapped["Company"] = relationship(
        back_populates="loan_simulations")
