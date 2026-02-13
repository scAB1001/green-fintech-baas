"""Pytest configuration and fixtures."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> Generator:
    """Provide FastAPI test client."""
    with TestClient(app) as c:
        yield c
