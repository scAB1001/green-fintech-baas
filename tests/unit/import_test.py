# tests/unit/import_test.py
"""Verify that the package can be imported."""

from __future__ import annotations

import pytest


@pytest.mark.unit
def test_import():
    """Test that app module can be imported."""
    try:
        import app

        assert app.__version__ == "0.1.0"
    except ImportError:
        pytest.fail("Failed to import app module")
