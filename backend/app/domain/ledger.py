"""Pure domain functions for customer ledger calculations.

RULES (from docs/01_PRD.md & docs/06_ENGINEERING_RULES.md):
- Outstanding balance = valid posted credit sales - valid posted repayments.
- All amounts must be integer paise.
- Overpayment is strictly rejected by default.
"""

from typing import Any, Dict, List, Tuple


def calculate_customer_balance(entries: List[Dict[str, Any]]) -> Tuple[int, int, int]:
    """Compute (outstanding_paise, total_credit_paise, total_repaid_paise).
    
    Returns:
        tuple: (outstanding_balance_paise, total_credit_paise, total_repaid_paise)
    """
    total_credit = 0
    total_repaid = 0

    for entry in entries:
        if entry.get("status", "posted") != "posted":
            continue

        entry_type = entry.get("entry_type")
        amount = entry.get("amount_paise", 0)

        if not isinstance(amount, int):
            raise TypeError(f"amount_paise must be integer, got {type(amount)}")

        if amount < 0:
            raise ValueError(f"Entry amount_paise cannot be negative: {amount}")

        if entry_type == "credit_sale":
            total_credit += amount
        elif entry_type == "repayment":
            total_repaid += amount

    outstanding = max(0, total_credit - total_repaid)
    return outstanding, total_credit, total_repaid


def validate_repayment_amount(current_outstanding_paise: int, repayment_amount_paise: int) -> None:
    """Validate that repayment amount is positive and does not exceed outstanding balance."""
    if not isinstance(repayment_amount_paise, int):
        raise TypeError("Repayment amount must be an integer (paise)")

    if repayment_amount_paise <= 0:
        raise ValueError("Repayment amount must be greater than zero")

    if repayment_amount_paise > current_outstanding_paise:
        raise ValueError(
            f"Repayment amount ({repayment_amount_paise} paise) exceeds current outstanding balance "
            f"({current_outstanding_paise} paise). Overpayment is not permitted."
        )
