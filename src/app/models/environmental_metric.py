
from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from . import Company  # Import the Company model for the relationship


class EnvironmentalMetric(Base):
    __tablename__ = "environmental_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"))
    reporting_year: Mapped[int] = mapped_column(Integer, nullable=False)
    energy_consumption_mwh: Mapped[float] = mapped_column(Numeric(10, 2))
    carbon_emissions_tco2e: Mapped[float] = mapped_column(Numeric(10, 2))
    water_usage_m3: Mapped[float | None] = mapped_column(Numeric(10, 2))
    waste_generated_tonnes: Mapped[float |
                                   None] = mapped_column(Numeric(10, 2))

    # Composite unique constraint
    __table_args__ = (UniqueConstraint(
        'company_id', 'reporting_year', name='uq_company_year'),)

    # Relationship
    company: Mapped["Company"] = relationship(
        back_populates="environmental_metrics")
