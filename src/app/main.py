# src/app/main.py
"""Main FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import companies
from app.core.config import settings


def create_application() -> FastAPI:
    """Application factory pattern."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint with API information."""
        return {
            "message": "Welcome to the Green FinTech BaaS Simulator API",
            "docs": "/docs",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/health", tags=["Monitoring"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "version": settings.VERSION,
        }

    app.include_router(
        companies.router, prefix="/api/v1/companies", tags=["companies"])

    return app


app = create_application()
