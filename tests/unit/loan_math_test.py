# tests/unit/loan_math_test.py
import pytest

from app.services.loan_simulation_service import LoanSimulationService


@pytest.mark.unit
def test_calculate_green_rate_optimal_conditions():
    """
    Verify math for a company with low emissions and high renewable national grid.
    """
    eps, final_rate = LoanSimulationService.calculate_green_rate(
        emissions_kt=500.0,  # Very low regional emissions (E_loc = 90)
        total_consumption=1000.0,
        renew_consumption=800.0,  # 80% renewable national grid (S_nat = 80)
        base_rate=8.0,
        max_discount=2.5,
    )

    # EPS = (80 * 0.3) + (90 * 0.7) = 24 + 63 = 87
    assert eps == 87.0

    # Discount = (87 / 100) * 2.5 = 2.175
    # Final Rate = 8.0 - 2.175 = 5.825 -> rounded to 5.83
    assert final_rate == 5.83


@pytest.mark.unit
def test_calculate_green_rate_worst_conditions():
    """Verify math bounds when emissions exceed the 5000kt cap."""
    eps, final_rate = LoanSimulationService.calculate_green_rate(
        emissions_kt=6000.0,  # Exceeds cap (E_loc = 0)
        total_consumption=1000.0,
        renew_consumption=0.0,  # 0% renewable (S_nat = 0)
        base_rate=8.0,
        max_discount=2.5,
    )

    assert eps == 0.0
    assert final_rate == 8.0  # Receives no discount
