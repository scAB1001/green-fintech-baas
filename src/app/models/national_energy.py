# src/app/models/national_energy.py
"""Company model for financial entities."""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NationalEnergy(Base):  # type: ignore
    __tablename__ = "national_energy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    country: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    energy_type: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    energy_consumption: Mapped[float] = mapped_column(Float, default=0.0)
    co2_emission: Mapped[float] = mapped_column(Float, default=0.0)

    def __repr__(self) -> str:
        return f"<NationalEnergy(country='{self.country}', \
            type='{self.energy_type}', year={self.year})>"
