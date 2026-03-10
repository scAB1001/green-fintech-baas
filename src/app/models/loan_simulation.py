# src/app/models/loan_simulation.py
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

from . import Company


class LoanSimulation(Base):  # type: ignore
    __tablename__ = "loan_simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )

    # Loan parameters
    loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)

    # Financial and ESG metrics
    base_rate: Mapped[float] = mapped_column(Float, nullable=False)
    applied_rate: Mapped[float] = mapped_column(Float, nullable=False)
    esg_score: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_carbon_savings: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    simulation_parameters: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationship
    company: Mapped["Company"] = relationship(back_populates="loan_simulations")

    def __repr__(self) -> str:
        return f"<LoanSimulation(id={self.id}, \
            company_id={self.company_id}, esg_score={self.esg_score})>"
