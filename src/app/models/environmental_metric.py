# src/app/models/environmental_metric.py
"""
Environmental Metric Entity Model.



This module defines the SQLAlchemy 2.0 ORM model for storing a company's
yearly Environmental, Social, and Governance (ESG) performance data.
It establishes a strict many-to-one relationship with the `Company` root aggregate.
"""

from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Imported to establish the bidirectional ORM relationship
from . import Company


class EnvironmentalMetric(Base):  # type: ignore
    """
    SQLAlchemy ORM model representing yearly environmental performance data.

    This model enforces a strict composite unique constraint to guarantee that
    a single corporate entity can only have one ESG record per reporting year,
    preventing duplicate aggregations during the loan simulation math.

    Attributes:
        id (int): The internal PostgreSQL primary key.
        company_id (int): The foreign key linking to the parent corporate entity.
        reporting_year (int): The 4-digit calendar year the metrics apply to.
        energy_consumption_mwh (float): Total energy usage in Megawatt-hours.
        carbon_emissions_tco2e (float): Total emissions in tonnes of CO2 equivalent.
        water_usage_m3 (float | None): Total water usage in cubic meters (optional).
        waste_generated_tonnes (float | None): Total waste in tonnes (optional).
    """

    __tablename__ = "environmental_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # We enforce cascading deletes at the database level. If the parent Company
    # is hard-deleted, PostgreSQL will automatically purge these child metrics
    # without requiring additional ORM queries.
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )
    reporting_year: Mapped[int] = mapped_column(Integer, nullable=False)

    energy_consumption_mwh: Mapped[float] = mapped_column(Float, default=0.0)
    carbon_emissions_tco2e: Mapped[float] = mapped_column(Float, default=0.0)
    water_usage_m3: Mapped[float | None] = mapped_column(Float, nullable=True)
    waste_generated_tonnes: Mapped[float |
                                   None] = mapped_column(Float, nullable=True)

    # Business Rule: A company can only report one set of metrics per year.
    # We enforce this mathematically at the database level using a composite constraint.
    __table_args__ = (
        UniqueConstraint("company_id", "reporting_year",
                         name="uq_company_year"),
    )

    company: Mapped["Company"] = relationship(
        back_populates="environmental_metrics")

    def __repr__(self) -> str:
        """
        Provides a developer-friendly string representation of the metric instance.

        Returns:
            str: A formatted string containing the parent company ID and reporting year.
        """
        return f"<EnvMetric(company_id={self.company_id}, year={self.reporting_year})>"
