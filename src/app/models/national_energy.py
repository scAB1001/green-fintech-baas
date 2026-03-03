"""Company model for financial entities."""
from sqlalchemy import Column, Float, Integer, String

from app.database import Base


class NationalEnergy(Base):
    __tablename__ = "national_energy"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String, index=True, nullable=False)
    energy_type = Column(String, nullable=False)
    year = Column(Integer, index=True, nullable=False)
    energy_consumption = Column(Float, default=0.0)
    co2_emission = Column(Float, default=0.0)

    def __repr__(self) -> str:
        return ""
