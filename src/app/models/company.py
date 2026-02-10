# src/app/models/company.py
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Company(Base):
    """Company model representing a business entity."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    companies_house_id: Mapped[str] = mapped_column(
        String(8), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_sector: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(100))

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}')>"
