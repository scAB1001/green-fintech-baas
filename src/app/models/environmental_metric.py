# src/app/models/environmental_metric.py
from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from . import Company


class EnvironmentalMetric(Base):
    __tablename__ = "environmental_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"))
    reporting_year: Mapped[int] = mapped_column(Integer, nullable=False)

    energy_consumption_mwh: Mapped[float] = mapped_column(Float, default=0.0)
    carbon_emissions_tco2e: Mapped[float] = mapped_column(Float, default=0.0)
    water_usage_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    waste_generated_tonnes: Mapped[float |
                                   None] = mapped_column(Float, nullable=True)

    __table_args__ = (UniqueConstraint(
        'company_id', 'reporting_year', name='uq_company_year'),)

    company: Mapped["Company"] = relationship(
        back_populates="environmental_metrics")

    def __repr__(self) -> str:
        return f"<EnvMetric(company_id={self.company_id}, year={self.reporting_year})>"
