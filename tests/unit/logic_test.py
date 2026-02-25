# tests/unit/logic_test.py
import pytest


def calculate_simple_score(emissions: float, target: float) -> bool:
    return emissions <= target


@pytest.mark.unit
def test_score_logic():
    """Verify core scoring math without any DB connection."""
    assert calculate_simple_score(100, 150) is True
    assert calculate_simple_score(200, 150) is False
