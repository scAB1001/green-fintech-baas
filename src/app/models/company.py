"""Company model for financial entities."""
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# This prevent circular imports at runtime
if TYPE_CHECKING:
    from .environmental_metric import EnvironmentalMetric
    from .loan_simulation import LoanSimulation


class Company(Base):
    """Represents a company/business entity."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    companies_house_id: Mapped[str] = mapped_column(
        String(8),
        unique=True,
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_sector: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(100))

    environmental_metrics: Mapped[list["EnvironmentalMetric"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    loan_simulations: Mapped[list["LoanSimulation"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}')>"
