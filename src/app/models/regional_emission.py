# src/app/models/regional_emission.py
"""Regional Emission model for emission data by region."""
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RegionalEmission(Base):
    __tablename__ = "regional_emissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    local_authority: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    industry_total: Mapped[float] = mapped_column(Float, default=0.0)
    commercial_total: Mapped[float] = mapped_column(Float, default=0.0)
    public_sector_total: Mapped[float] = mapped_column(Float, default=0.0)
    domestic_total: Mapped[float] = mapped_column(Float, default=0.0)
    transport_total: Mapped[float] = mapped_column(Float, default=0.0)
    agriculture_total: Mapped[float] = mapped_column(Float, default=0.0)
    grand_total: Mapped[float] = mapped_column(Float, default=0.0)

    def __repr__(self) -> str:
        return f"<RegionalEmission(authority='{self.local_authority}', \
            year={self.year}, total={self.grand_total})>"
