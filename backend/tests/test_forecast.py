"""Unit tests for the pure deterministic forecast engine.

Covers:
- Formula: closing[d] = opening[d] + inflows[d] - outflows[d]
- Month boundaries and leap years
- Multiple movements on same date
- Zero-movement days
- Deficit detection (below_zero) and safety buffer breaches (below_safety_buffer)
- Contributor reference attribution
- Filtering of past movements (avoid double-counting with opening balance)
- Strict integer paise validation (reject float)
"""

from datetime import date
import pytest
from app.domain.forecast import (
    ForecastMovement,
    generate_forecast,
    normalize_movement,
)


def test_basic_deterministic_forecast_calculation():
    """Verify daily closing balance formula strictly matches: closing = opening + in - out."""
    start_date = "2026-10-17"
    opening_cash = 1500000  # ₹15,000

    inflows = [
        {"date": "2026-10-18", "amount_paise": 500000, "source_type": "customer_collection", "id": "in_1", "description": "Customer A"},
        {"date": "2026-10-20", "amount_paise": 1000000, "source_type": "customer_collection", "id": "in_2", "description": "Customer B"},
    ]
    outflows = [
        {"date": "2026-10-19", "amount_paise": 800000, "source_type": "supplier_bill", "id": "out_1", "description": "Supplier X"},
    ]

    res = generate_forecast(
        start_date=start_date,
        opening_cash_paise=opening_cash,
        inflows=inflows,
        outflows=outflows,
        safety_buffer_paise=1000000,  # ₹10,000
        horizon_days=5,
    )

    assert res.horizon_days == 5
    assert len(res.days) == 5

    # Day 0: 2026-10-17: In=0, Out=0 -> Closing = 15,000
    d0 = res.days[0]
    assert d0.date == "2026-10-17"
    assert d0.opening_balance_paise == 1500000
    assert d0.inflows_paise == 0
    assert d0.outflows_paise == 0
    assert d0.closing_balance_paise == 1500000
    assert not d0.below_zero
    assert not d0.below_safety_buffer

    # Day 1: 2026-10-18: In=5,000, Out=0 -> Closing = 20,000
    d1 = res.days[1]
    assert d1.date == "2026-10-18"
    assert d1.opening_balance_paise == 1500000
    assert d1.inflows_paise == 500000
    assert d1.closing_balance_paise == 2000000
    assert len(d1.contributors) == 1
    assert d1.contributors[0].source_id == "in_1"

    # Day 2: 2026-10-19: In=0, Out=8,000 -> Closing = 12,000
    d2 = res.days[2]
    assert d2.date == "2026-10-19"
    assert d2.opening_balance_paise == 2000000
    assert d2.outflows_paise == 800000
    assert d2.closing_balance_paise == 1200000

    # Day 3: 2026-10-20: In=10,000, Out=0 -> Closing = 22,000
    d3 = res.days[3]
    assert d3.date == "2026-10-20"
    assert d3.opening_balance_paise == 1200000
    assert d3.inflows_paise == 1000000
    assert d3.closing_balance_paise == 2200000

    # Day 4: 2026-10-21: In=0, Out=0 -> Closing = 22,000
    d4 = res.days[4]
    assert d4.date == "2026-10-21"
    assert d4.opening_balance_paise == 2200000
    assert d4.closing_balance_paise == 2200000


def test_month_boundary_and_leap_year():
    """Verify continuity across leap day Feb 29 and month rollover."""
    # 2024 is a leap year (Feb 29 exists)
    start_date = "2024-02-28"
    opening_cash = 500000

    inflows = [
        {"date": "2024-02-29", "amount_paise": 200000, "source_type": "customer_collection", "id": "leap_in", "description": "Leap day"},
        {"date": "2024-03-01", "amount_paise": 100000, "source_type": "customer_collection", "id": "mar_in", "description": "March first"},
    ]

    res = generate_forecast(
        start_date=start_date,
        opening_cash_paise=opening_cash,
        inflows=inflows,
        outflows=[],
        horizon_days=3,
    )

    assert [d.date for d in res.days] == ["2024-02-28", "2024-02-29", "2024-03-01"]
    assert res.days[0].closing_balance_paise == 500000
    assert res.days[1].closing_balance_paise == 700000
    assert res.days[2].closing_balance_paise == 800000


def test_same_day_multiple_movements():
    """Verify aggregating multiple inflows and outflows occurring on the exact same date."""
    start_date = "2026-10-17"
    opening_cash = 2000000

    inflows = [
        ForecastMovement(date="2026-10-18", amount_paise=300000, source_type="customer_collection", source_id="c1", description="Cust 1"),
        ForecastMovement(date="2026-10-18", amount_paise=200000, source_type="customer_collection", source_id="c2", description="Cust 2"),
    ]
    outflows = [
        ForecastMovement(date="2026-10-18", amount_paise=100000, source_type="supplier_bill", source_id="s1", description="Bill 1"),
        ForecastMovement(date="2026-10-18", amount_paise=400000, source_type="supplier_bill", source_id="s2", description="Bill 2"),
    ]

    res = generate_forecast(
        start_date=start_date,
        opening_cash_paise=opening_cash,
        inflows=inflows,
        outflows=outflows,
        horizon_days=2,
    )

    day1 = res.days[1]
    assert day1.inflows_paise == 500000
    assert day1.outflows_paise == 500000
    assert day1.closing_balance_paise == 2000000
    assert len(day1.contributors) == 4


def test_deficit_and_safety_buffer_breach():
    """Verify below_zero and below_safety_buffer flags when cash drops."""
    start_date = "2026-10-17"
    opening_cash = 1000000  # ₹10,000
    safety_buffer = 1500000  # ₹15,000

    outflows = [
        {"date": "2026-10-18", "amount_paise": 800000, "source_type": "supplier_bill", "id": "bill_1", "description": "Bill 1"},  # closing = 2,000 (< 15,000)
        {"date": "2026-10-19", "amount_paise": 500000, "source_type": "supplier_bill", "id": "bill_2", "description": "Bill 2"},  # closing = -3,000 (< 0)
    ]

    res = generate_forecast(
        start_date=start_date,
        opening_cash_paise=opening_cash,
        inflows=[],
        outflows=outflows,
        safety_buffer_paise=safety_buffer,
        horizon_days=3,
    )

    assert res.shortage_detected is True
    assert res.buffer_breached is True
    assert res.lowest_dip_paise == -300000
    assert res.lowest_dip_date == "2026-10-19"

    # Day 0: 10,000 (< 15,000 buffer, not below zero)
    assert res.days[0].below_zero is False
    assert res.days[0].below_safety_buffer is True

    # Day 1: 2,000 (< 15,000 buffer, not below zero)
    assert res.days[1].below_zero is False
    assert res.days[1].below_safety_buffer is True

    # Day 2: -3,000 (below zero AND below safety buffer)
    assert res.days[2].below_zero is True
    assert res.days[2].below_safety_buffer is True


def test_prevent_double_counting_prior_movements():
    """Verify movements dated prior to forecast start date are ignored."""
    start_date = "2026-10-17"
    opening_cash = 500000

    inflows = [
        {"date": "2026-10-15", "amount_paise": 9999999, "source_type": "customer_collection", "id": "old_1", "description": "Old collection"},
        {"date": "2026-10-17", "amount_paise": 100000, "source_type": "customer_collection", "id": "today_1", "description": "Today collection"},
    ]
    outflows = [
        {"date": "2026-10-16", "amount_paise": 8888888, "source_type": "supplier_bill", "id": "old_out", "description": "Old bill"},
    ]

    res = generate_forecast(
        start_date=start_date,
        opening_cash_paise=opening_cash,
        inflows=inflows,
        outflows=outflows,
        horizon_days=1,
    )

    # Old movements were discarded; only today's 100000 was counted
    assert res.days[0].inflows_paise == 100000
    assert res.days[0].outflows_paise == 0
    assert res.days[0].closing_balance_paise == 600000


def test_integer_paise_and_type_guards():
    """Verify non-integer amounts and negative amounts trigger TypeError/ValueError."""
    with pytest.raises(TypeError):
        normalize_movement({"date": "2026-10-17", "amount_paise": 150.50, "description": "Float"})

    with pytest.raises(ValueError):
        normalize_movement({"date": "2026-10-17", "amount_paise": -500, "description": "Negative"})

    with pytest.raises(TypeError):
        generate_forecast(start_date="2026-10-17", opening_cash_paise=150.5, inflows=[], outflows=[])
