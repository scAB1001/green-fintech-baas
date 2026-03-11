# src/app/database/__init__.py
"""
Database Persistence Layer.

Exposes the core session factory, the declarative Base for ORM models,
and the FastAPI dependency for asynchronous session injection.
"""

from app.database.session import AsyncSessionLocal, Base, engine, get_db

__all__ = ["AsyncSessionLocal", "Base", "engine", "get_db"]
