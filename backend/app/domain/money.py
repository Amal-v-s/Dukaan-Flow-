"""Domain logic for money representation and formatting in DukaanFlow.

RULES (from docs/06_ENGINEERING_RULES.md & docs/DESIGN.md):
- Store money strictly as integer paise (amount_paise).
- Never use binary floating-point (float) for currency arithmetic.
- Format for display using Indian numbering system (e.g., ₹84,500, ₹1,48,200).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union


def inr_to_paise(amount_inr: Union[str, int, Decimal]) -> int:
    """Convert an INR value (string or Decimal or int) to integer paise.
    
    Never pass raw float to avoid IEEE 754 precision issues.
    """
    if isinstance(amount_inr, float):
        raise TypeError("Binary float is strictly prohibited for currency. Use str or Decimal.")
    
    d = Decimal(str(amount_inr))
    paise = (d * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(paise)


def paise_to_inr_decimal(paise: int) -> Decimal:
    """Convert integer paise to Decimal INR."""
    if not isinstance(paise, int):
        raise TypeError(f"Paise must be an integer, got {type(paise)}")
    return (Decimal(paise) / Decimal("100")).quantize(Decimal("0.01"))


def format_inr(paise: int, include_symbol: bool = True, show_paise_if_zero: bool = False) -> str:
    """Format paise into Indian currency notation.
    
    Examples:
        format_inr(8450000) -> "₹84,500"
        format_inr(14820000) -> "₹1,48,200"
        format_inr(-1000000) -> "-₹10,000"
        format_inr(125050, show_paise_if_zero=False) -> "₹1,250.50"
    """
    if not isinstance(paise, int):
        raise TypeError(f"Paise must be an integer, got {type(paise)}")
    
    is_negative = paise < 0
    abs_paise = abs(paise)
    
    rupees = abs_paise // 100
    rem_paise = abs_paise % 100
    
    # Format the rupee part with Indian numbering system (3 digits, then groups of 2)
    s = str(rupees)
    if len(s) <= 3:
        formatted_rupees = s
    else:
        last_three = s[-3:]
        remaining = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_rupees = ",".join(groups) + "," + last_three
    
    if rem_paise > 0 or show_paise_if_zero:
        formatted_str = f"{formatted_rupees}.{rem_paise:02d}"
    else:
        formatted_str = formatted_rupees
        
    prefix = ""
    if is_negative:
        prefix = "-"
    
    symbol = "₹" if include_symbol else ""
    return f"{prefix}{symbol}{formatted_str}"


format_paise_to_inr = format_inr
