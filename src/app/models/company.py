# src/app/models/company.py
"""
Company Entity Model.



This module defines the SQLAlchemy 2.0 ORM model for a corporate entity.
It serves as the central root aggregate in our Domain-Driven Design schema,
linking a company's financial identity to its environmental performance metrics
and generated loan simulations.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# TYPE_CHECKING is always False at runtime. We use it here to provide static
# type hints for our ORM relationships without triggering circular import
# errors between closely coupled database models.
if TYPE_CHECKING:
    from .environmental_metric import EnvironmentalMetric
    from .loan_simulation import LoanSimulation


class Company(Base):  # type: ignore
    """
    SQLAlchemy ORM model representing a corporate entity.

    Attributes:
        id (int): The internal PostgreSQL primary key.
        companies_house_id (str):
            The official, unique UK Companies House registration number.
        name (str): The legally registered name of the business.
        business_sector (str):
            The industry classification (e.g., Manufacturing, Finance).
        location (str): The UK local authority or region of primary operation.
        opencorporates_url (str | None):
            A direct link to the OpenCorporates registry profile.
        environmental_metrics (list[EnvironmentalMetric]):
            One-to-many relationship to yearly ESG data.
        loan_simulations (list[LoanSimulation]): One-to-many relationship to SLL quotes.
    """

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # We enforce an 8-character string constraint to match the standard
    # UK Companies House format, applying a unique index for fast lookups.
    companies_house_id: Mapped[str] = mapped_column(
        String(8), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_sector: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(100))
    opencorporates_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # We enforce referential integrity at the ORM level using cascade deletes.
    # If a Company record is hard-deleted, all of its associated SLL quotes
    # and ESG metrics are automatically purged from the database to prevent orphans.
    environmental_metrics: Mapped[list["EnvironmentalMetric"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    loan_simulations: Mapped[list["LoanSimulation"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """
        Provides a safe, developer-friendly string representation of the object
        for debugging, omitting sensitive or massive relationship data.

        Returns:
            str: A formatted string containing the ID, name, and CH number.
        """
        return (
            f"<Company(id={self.id}, name='{self.name}', "
            f"ch_id='{self.companies_house_id}')>"
        )
