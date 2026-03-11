# src/app/models/__init__.py
"""
Data Models Manifest.



Aggregates all SQLAlchemy ORM models into a single namespace. This is
critically required for Alembic to detect and generate schema migrations
via 'target_metadata'.
"""

from app.models.company import Company
from app.models.environmental_metric import EnvironmentalMetric
from app.models.loan_simulation import LoanSimulation
from app.models.national_energy import NationalEnergy
from app.models.regional_emission import RegionalEmission

# Explicitly exposing for Alembic and high-level service imports
__all__ = [
    "Company",
    "EnvironmentalMetric",
    "LoanSimulation",
    "NationalEnergy",
    "RegionalEmission",
]
