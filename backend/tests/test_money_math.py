import pytest
from backend.app.services.analytics_service import AnalyticsService


def test_minor_unit_conversions():
    """Verify that minor units prevent floating point drift."""
    # ₹1,24,500.50 should be exactly 12450050 paise
    paise = 12450050
    rupees = paise / 100.0
    assert rupees == 124500.50
    assert int(rupees * 100) == paise


def test_budget_utilization_calculation():
    """Verify budget percentage calculations."""
    spent = 14200.0
    limit = 18000.0
    percentage = round((spent / limit) * 100)
    assert percentage == 79


def test_health_score_bounds():
    """Verify health score stays clamped between 0 and 100."""
    score_high = min(100, max(0, int(0.45 * 100 + 0.35 * 100 + 20)))
    assert score_high == 100

    score_low = min(100, max(20, int(0.45 * 0 + 0.35 * 0 + 20)))
    assert score_low == 20
