"""Pure deterministic cash-flow forecast domain calculations.

RULES (from docs/01_PRD.md, docs/02_TRD.md, & docs/06_ENGINEERING_RULES.md):
- 14-day cash-flow forecast is calculated strictly in deterministic, unit-tested Python functions.
- NO LLM or AI arithmetic for balances, projections, or shortage detection.
- All monetary values must be integer paise (amount_paise). Never use binary float.
- Avoid double-counting: filter out movements dated prior to forecast start date
  (as they are already reflected in the verified opening cash balance).
- Closing balance formula: closing[d] = opening[d] + inflows[d] - outflows[d].
- Opening balance for day d (d > 0) is closing[d-1].
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Union


@dataclass(frozen=True)
class ForecastContributor:
    """Represents a specific transaction, bill, or collection contributing to daily cash movement."""
    source_type: str  # 'customer_collection', 'supplier_bill', 'expense', 'hypothetical'
    source_id: str
    description: str
    amount_paise: int


@dataclass(frozen=True)
class ForecastMovement:
    """An expected future cash movement (inflow or outflow)."""
    date: str  # ISO-8601 format: YYYY-MM-DD
    amount_paise: int
    source_type: str
    source_id: str
    description: str


@dataclass
class ForecastDay:
    """Projected cash position and movements for a single calendar day."""
    date: str  # ISO-8601 format: YYYY-MM-DD
    opening_balance_paise: int
    inflows_paise: int
    outflows_paise: int
    closing_balance_paise: int
    below_zero: bool
    below_safety_buffer: bool
    contributors: List[ForecastContributor] = field(default_factory=list)


@dataclass
class ForecastResult:
    """Complete multi-day deterministic forecast output."""
    horizon_days: int
    opening_cash_paise: int
    safety_buffer_paise: int
    days: List[ForecastDay]
    lowest_dip_paise: int
    lowest_dip_date: str
    shortage_detected: bool  # True if any day has closing < 0
    buffer_breached: bool   # True if any day has closing < safety_buffer_paise
    assumptions: List[str]


def normalize_movement(item: Union[ForecastMovement, Dict[str, Any]]) -> ForecastMovement:
    """Validate and normalize a cash movement into a ForecastMovement."""
    if isinstance(item, ForecastMovement):
        date_str = item.date
        amount = item.amount_paise
        source_type = item.source_type
        source_id = item.source_id
        description = item.description
    elif isinstance(item, dict):
        date_str = item.get("date") or item.get("due_date")
        amount = item.get("amount_paise", 0)
        source_type = item.get("source_type", "unknown")
        source_id = item.get("source_id", item.get("id", "unknown"))
        description = item.get("description", "")
    else:
        raise TypeError(f"Expected ForecastMovement or dict, got {type(item)}")

    if not isinstance(date_str, str) or len(date_str.strip()) == 0:
        raise ValueError(f"Movement date must be a non-empty ISO string: {date_str}")

    # Validate ISO date format
    try:
        date.fromisoformat(date_str)
    except ValueError as err:
        raise ValueError(f"Invalid ISO date format '{date_str}': {err}")

    if not isinstance(amount, int):
        raise TypeError(f"amount_paise must be an integer, got {type(amount)}: {amount}")

    if amount < 0:
        raise ValueError(f"amount_paise cannot be negative: {amount}")

    return ForecastMovement(
        date=date_str,
        amount_paise=amount,
        source_type=str(source_type),
        source_id=str(source_id),
        description=str(description),
    )


def generate_forecast(
    start_date: Union[date, str],
    opening_cash_paise: int,
    inflows: List[Union[ForecastMovement, Dict[str, Any]]],
    outflows: List[Union[ForecastMovement, Dict[str, Any]]],
    safety_buffer_paise: int = 0,
    horizon_days: int = 14,
    assumptions: Optional[List[str]] = None,
) -> ForecastResult:
    """Generate a pure deterministic day-by-day cash-flow projection.
    
    Args:
        start_date: Forecast starting date (inclusive, Day 1).
        opening_cash_paise: Verified cash balance on start_date morning.
        inflows: Future expected cash collections/receipts.
        outflows: Future scheduled cash payments/bills.
        safety_buffer_paise: Merchant configured liquidity safety threshold.
        horizon_days: Number of projection days (typically 14).
        assumptions: Optional list of explicit merchant assumptions.
        
    Returns:
        ForecastResult with day-by-day closing balances and shortage flags.
    """
    if isinstance(start_date, str):
        parsed_start = date.fromisoformat(start_date)
    elif isinstance(start_date, date):
        parsed_start = start_date
    else:
        raise TypeError(f"start_date must be date or ISO string, got {type(start_date)}")

    if not isinstance(opening_cash_paise, int):
        raise TypeError(f"opening_cash_paise must be integer paise, got {type(opening_cash_paise)}")

    if not isinstance(safety_buffer_paise, int):
        raise TypeError(f"safety_buffer_paise must be integer paise, got {type(safety_buffer_paise)}")

    if safety_buffer_paise < 0:
        raise ValueError("safety_buffer_paise cannot be negative")

    if not isinstance(horizon_days, int) or horizon_days <= 0:
        raise ValueError("horizon_days must be a positive integer >= 1")

    # Determine horizon window [start_date, end_date)
    end_date = parsed_start + timedelta(days=horizon_days)
    start_iso = parsed_start.isoformat()
    end_iso = end_date.isoformat()

    # Index inflows by date, ignoring historical movements prior to start_date
    inflows_by_date: Dict[str, List[ForecastMovement]] = {}
    for raw in inflows:
        norm = normalize_movement(raw)
        # Avoid double-counting: movements before start_date are already in opening_cash_paise
        if norm.date < start_iso or norm.date >= end_iso:
            continue
        inflows_by_date.setdefault(norm.date, []).append(norm)

    # Index outflows by date, ignoring historical movements prior to start_date
    outflows_by_date: Dict[str, List[ForecastMovement]] = {}
    for raw in outflows:
        norm = normalize_movement(raw)
        if norm.date < start_iso or norm.date >= end_iso:
            continue
        outflows_by_date.setdefault(norm.date, []).append(norm)

    days: List[ForecastDay] = []
    current_balance = opening_cash_paise
    lowest_dip_paise = opening_cash_paise
    lowest_dip_date = start_iso
    shortage_detected = False
    buffer_breached = False

    for i in range(horizon_days):
        current_date = parsed_start + timedelta(days=i)
        current_iso = current_date.isoformat()
        day_opening = current_balance

        day_inflows = inflows_by_date.get(current_iso, [])
        day_outflows = outflows_by_date.get(current_iso, [])

        total_inflow = sum(m.amount_paise for m in day_inflows)
        total_outflow = sum(m.amount_paise for m in day_outflows)

        closing = day_opening + total_inflow - total_outflow

        is_below_zero = closing < 0
        is_below_buffer = closing < safety_buffer_paise

        if is_below_zero:
            shortage_detected = True
        if is_below_buffer:
            buffer_breached = True

        # Track lowest dip
        if i == 0 or closing < lowest_dip_paise:
            lowest_dip_paise = closing
            lowest_dip_date = current_iso

        # Build contributors list
        contributors: List[ForecastContributor] = []
        for m in day_inflows:
            contributors.append(
                ForecastContributor(
                    source_type=m.source_type,
                    source_id=m.source_id,
                    description=m.description,
                    amount_paise=m.amount_paise,
                )
            )
        for m in day_outflows:
            contributors.append(
                ForecastContributor(
                    source_type=m.source_type,
                    source_id=m.source_id,
                    description=m.description,
                    amount_paise=m.amount_paise,
                )
            )

        days.append(
            ForecastDay(
                date=current_iso,
                opening_balance_paise=day_opening,
                inflows_paise=total_inflow,
                outflows_paise=total_outflow,
                closing_balance_paise=closing,
                below_zero=is_below_zero,
                below_safety_buffer=is_below_buffer,
                contributors=contributors,
            )
        )

        current_balance = closing

    default_assumptions = [
        "Opening cash reflects verified register balance on forecast start date.",
        "Expected customer collections are estimates based on agreed due dates.",
        "Supplier bills must be settled on or before their stated due dates.",
    ]

    return ForecastResult(
        horizon_days=horizon_days,
        opening_cash_paise=opening_cash_paise,
        safety_buffer_paise=safety_buffer_paise,
        days=days,
        lowest_dip_paise=lowest_dip_paise,
        lowest_dip_date=lowest_dip_date,
        shortage_detected=shortage_detected,
        buffer_breached=buffer_breached,
        assumptions=assumptions or default_assumptions,
    )
