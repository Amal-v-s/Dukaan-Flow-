import pytest
from decimal import Decimal
from app.domain.money import inr_to_paise, paise_to_inr_decimal, format_inr


def test_inr_to_paise_integer():
    assert inr_to_paise(100) == 10000
    assert inr_to_paise(0) == 0
    assert inr_to_paise(-50) == -5000


def test_inr_to_paise_string_decimal():
    assert inr_to_paise("148.50") == 14850
    assert inr_to_paise("0.75") == 75
    assert inr_to_paise("100000.00") == 10000000


def test_inr_to_paise_decimal():
    assert inr_to_paise(Decimal("1500.25")) == 150025


def test_inr_to_paise_rejects_float():
    with pytest.raises(TypeError, match="Binary float is strictly prohibited"):
        inr_to_paise(14.50)


def test_paise_to_inr_decimal():
    assert paise_to_inr_decimal(1500000) == Decimal("15000.00")
    assert paise_to_inr_decimal(75) == Decimal("0.75")
    assert paise_to_inr_decimal(-500) == Decimal("-5.00")


def test_format_inr_indian_grouping():
    # 84,500 rupees -> ₹84,500
    assert format_inr(8450000) == "₹84,500"

    # 1,48,200 rupees -> ₹1,48,200
    assert format_inr(14820000) == "₹1,48,200"

    # 10,00,000 rupees (10 Lakhs) -> ₹10,00,000
    assert format_inr(100000000) == "₹10,00,000"

    # Negative amount -> -₹10,000
    assert format_inr(-1000000) == "-₹10,000"

    # Zero -> ₹0
    assert format_inr(0) == "₹0"

    # With fractional paise
    assert format_inr(125050) == "₹1,250.50"


def test_format_inr_without_symbol():
    assert format_inr(8450000, include_symbol=False) == "84,500"
    assert format_inr(-1000000, include_symbol=False) == "-10,000"
