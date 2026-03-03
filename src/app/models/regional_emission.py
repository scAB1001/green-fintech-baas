"""Regional Emission model for emission data by region."""
from sqlalchemy import Column, Float, Integer, String

from app.database import Base


class RegionalEmission(Base):
    __tablename__ = "regional_emissions"

    id = Column(Integer, primary_key=True, index=True)
    local_authority = Column(String, index=True, nullable=False)
    year = Column(Integer, index=True, nullable=False)
    industry_total = Column(Float, default=0.0)
    commercial_total = Column(Float, default=0.0)
    public_sector_total = Column(Float, default=0.0)
    domestic_total = Column(Float, default=0.0)
    transport_total = Column(Float, default=0.0)
    agriculture_total = Column(Float, default=0.0)
    grand_total = Column(Float, default=0.0)

    def __repr__(self) -> str:
        return ""
