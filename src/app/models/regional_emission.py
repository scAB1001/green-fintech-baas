# src/app/models/regional_emission.py
"""
Regional Emission Reference Model.



This module defines the SQLAlchemy 2.0 ORM model for storing granular UK CO2
emissions data. It categorizes emissions by sector and local authority,
providing the regional baseline required to calculate the 'Location' factor
in the ESG loan simulation engine.
"""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RegionalEmission(Base):  # type: ignore
    """
    SQLAlchemy ORM model for regional UK emission datasets.

    This model stores historical emission data provided by government bodies.
    It is used as a lookup table to compare a specific company's performance
    against the average footprint of its primary operating region.

    Attributes:
        id (int): Internal primary key.
        local_authority (str): The name of the UK local authority (e.g., 'Leeds').
        year (int): The reporting year for the dataset.
        industry_total (float): CO2 emissions from industrial sources (ktCO2).
        commercial_total (float): CO2 emissions from commercial sources (ktCO2).
        public_sector_total (float): CO2 emissions from public administration.
        domestic_total (float): CO2 emissions from household/residential sources.
        transport_total (float): CO2 emissions from road and rail transport.
        agriculture_total (float): CO2 emissions from farming and land use.
        grand_total (float): The aggregate emission total for the region.
    """

    __tablename__ = "regional_emissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # We index local_authority and year as they are the primary join keys
    # used when fetching a baseline for a specific company's profile.
    local_authority: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    industry_total: Mapped[float] = mapped_column(Float, default=0.0)
    commercial_total: Mapped[float] = mapped_column(Float, default=0.0)
    public_sector_total: Mapped[float] = mapped_column(Float, default=0.0)
    domestic_total: Mapped[float] = mapped_column(Float, default=0.0)
    transport_total: Mapped[float] = mapped_column(Float, default=0.0)
    agriculture_total: Mapped[float] = mapped_column(Float, default=0.0)
    grand_total: Mapped[float] = mapped_column(Float, default=0.0)

    def __repr__(self) -> str:
        """
        Returns a concise string representation for logging and debugging.
        """
        return (
            f"<RegionalEmission(authority='{self.local_authority}', "
            f"year={self.year}, total={self.grand_total})>"
        )
