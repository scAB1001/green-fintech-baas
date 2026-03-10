# src/app/main.py
"""
Main FastAPI Application Factory.



This module serves as the entry point for the Green FinTech BaaS Simulator.
It utilizes the 'Application Factory' pattern to initialize the FastAPI
instance, configure essential middleware (CORS), and mount the domain-specific
API routers.

This structure facilitates better testability by allowing the creation of
isolated app instances for integration testing.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import companies
from app.core.config import settings


def create_application() -> FastAPI:
    """
    Constructs and configures the FastAPI application instance.

    Configures:
        - Global metadata (Title, Version).
        - CORS Middleware: Relaxed for local development, restricted for production.
        - Routing: Mounts versioned API endpoints.
        - Documentation: Enables Swagger (/docs) and ReDoc (/redoc).

    Returns:
        FastAPI: The fully configured application instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Cross-Origin Resource Sharing (CORS) Configuration.
    # In development, we allow all origins to facilitate frontend prototyping.
    # In production, this is limited to prevent unauthorised cross-site requests.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        """
        Root entry point for the API.

        Provides basic environment metadata and links to the interactive
        OpenAPI documentation.
        """
        return {
            "message": "Welcome to the Green FinTech BaaS Simulator API",
            "docs": "/docs",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/health", tags=["Monitoring"])
    async def health_check() -> dict[str, str]:
        """
        Liveness probe for orchestration and monitoring.

        Used by tools like Docker, Kubernetes, or Uptime monitors to verify
        that the service is operational and capable of handling traffic.
        """
        return {
            "status": "healthy",
            "version": settings.VERSION,
        }

    # API Routing Layer.
    # We prefix all company-related endpoints under /api/v1/companies to
    # maintain semantic versioning and logical domain separation.
    app.include_router(
        companies.router, prefix="/api/v1/companies", tags=["companies"])

    return app


# The singleton application instance used by the ASGI server (Uvicorn/Gunicorn).
app = create_application()
