import pytest
from datetime import date
from backend.app.services.ingestion_service import IngestionService


def test_merchant_category_rules():
    """Verify standard Indian payment descriptions normalize to canonical merchants."""
    merchant, cat, channel = IngestionService._resolve_merchant_and_category("UPI/SWIGGY/12345/LUNCH")
    assert merchant == "Swiggy"
    assert cat == "Food & Dining"
    assert channel == "UPI"

    merchant, cat, channel = IngestionService._resolve_merchant_and_category("POS/CROMA/BANGALORE/ELECTRONICS")
    assert merchant == "Croma Retail"
    assert cat == "Shopping"
    assert channel == "Card"

    merchant, cat, channel = IngestionService._resolve_merchant_and_category("ACH/ZERODHA/MONTHLY/SIP")
    assert channel == "NetBanking"


def test_date_parsing_variations():
    """Verify various Indian statement date formats parse correctly."""
    d1 = IngestionService._parse_date("03/02/2025")
    assert d1 == date(2025, 2, 3)

    d2 = IngestionService._parse_date("2025-01-31")
    assert d2 == date(2025, 1, 31)

    d3 = IngestionService._parse_date("15-01-2025")
    assert d3 == date(2025, 1, 15)
