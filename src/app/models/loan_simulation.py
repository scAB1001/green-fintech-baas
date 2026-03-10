# src/app/models/loan_simulation.py
"""
Loan Simulation Entity Model.



This module defines the SQLAlchemy 2.0 ORM model for storing generated
Sustainability-Linked Loan (SLL) quotes. It links the financial parameters
of a loan request to the calculated Environmental Performance Score (EPS)
and the resulting interest rate discount.
"""

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

# Imported to establish the bidirectional ORM relationship
from . import Company


class LoanSimulation(Base):  # type: ignore
    """
    SQLAlchemy ORM model representing a green loan simulation quote.

    This entity is effectively immutable once created. It serves as an audit
    trail for the exact financial and ESG metrics used to calculate the
    discounted interest rate at a specific point in time.

    Attributes:
        id (int): The internal PostgreSQL primary key.
        company_id (int): Foreign key linking to the parent corporate entity.
        loan_amount (float): The principal loan amount requested.
        term_months (int): The duration of the loan in months.
        base_rate (float): The standard market interest rate before ESG discounts.
        applied_rate (float): The final interest rate after the ESG margin ratchet.
        esg_score (float): The Environmental Performance Score (EPS) at quote time.
        estimated_carbon_savings (float | None): Projected carbon reduction.
        created_at (datetime): Database-generated timestamp of the simulation.
        simulation_parameters (str | None): JSON string of the exact mathematical input.
    """

    __tablename__ = "loan_simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Enforce cascading deletes so simulations are purged if the parent company
    # is removed from the system.
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
    estimated_carbon_savings: Mapped[float |
                                     None] = mapped_column(Float, nullable=True)

    # Metadata
    # func.now() delegates the timestamp generation directly to PostgreSQL,
    # avoiding timezone/clock drift issues across distributed FastAPI workers.
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    simulation_parameters: Mapped[str | None] = mapped_column(
        String, nullable=True)

    # Relationship
    company: Mapped["Company"] = relationship(
        back_populates="loan_simulations")

    def __repr__(self) -> str:
        """
        Provides a safe, developer-friendly string representation of the object.

        Returns:
            str: A formatted string containing the ID, company ID, and EPS score.
        """
        return (
            f"<LoanSimulation(id={self.id}, company_id={self.company_id}, "
            f"esg_score={self.esg_score})>"
        )
