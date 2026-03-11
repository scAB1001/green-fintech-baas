# src/app/models/national_energy.py
"""
National Energy Reference Model.

This module defines the SQLAlchemy 2.0 ORM model for storing macro-level
national energy consumption and CO2 emission datasets. This data acts as a
reference baseline when calculating a company's Environmental Performance Score.
"""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NationalEnergy(Base):  # type: ignore
    """
    SQLAlchemy ORM model representing national energy datasets.

    Unlike the Company or EnvironmentalMetric models, this table acts as an
    independent reference dictionary. It is queried during the loan simulation
    process to benchmark a specific corporate entity against national averages.

    Attributes:
        id (int): The internal PostgreSQL primary key.
        country (str): The name of the nation (e.g., 'United Kingdom').
        energy_type (str): The category of energy (e.g., 'Wind', 'Coal').
        year (int): The calendar year the data point represents.
        energy_consumption (float): Total energy consumption (TWh).
        co2_emission (float): Total carbon emissions (MtCO2e).
    """

    __tablename__ = "national_energy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Indexed for fast lookups when filtering by nation during math simulations
    country: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    energy_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Indexed because we frequently query baseline data for a specific reporting year
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    energy_consumption: Mapped[float] = mapped_column(Float, default=0.0)
    co2_emission: Mapped[float] = mapped_column(Float, default=0.0)

    def __repr__(self) -> str:
        """
        Provides a developer-friendly string representation of the model.

        Returns:
            str: A formatted string containing the country, energy type, and year.
        """
        return (
            f"<NationalEnergy(country='{self.country}', "
            f"type='{self.energy_type}', year={self.year})>"
        )
