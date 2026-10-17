"""Centralized helper to gather future cash-flow forecast inflows and outflows.

Ensures deterministic consistency across:
- Cash-flow forecast endpoint (/api/v1/cash-flow/forecast)
- Alert generation service (AlertService)
- What-If scenario simulator (ScenarioService)
"""

from typing import Any, Dict, List, Optional, Tuple
from app.services.phase2_service import list_plans


def gather_forecast_movements(
    customers: List[Dict[str, Any]],
    bills: List[Dict[str, Any]],
    plans: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extract deterministic future inflows and outflows.
    
    Inflows include:
    - Customer credit entries minus allocated shares from active repayment plans
    - Scheduled installments from active repayment plans
    
    Outflows include:
    - Unpaid supplier bills with remaining amount > 0
    """
    if plans is None:
        try:
            plans = list_plans()
        except Exception:
            plans = []

    allocations: Dict[str, int] = {}
    for plan in plans:
        if plan.get("status") != "cancelled":
            for source_id, amount in plan.get("source_allocations_paise", {}).items():
                allocations[source_id] = allocations.get(source_id, 0) + amount

    inflows: List[Dict[str, Any]] = []
    for c in customers:
        for entry in c.get("credit_entries", []):
            if entry.get("status", "posted") == "posted" and entry.get("entry_type") == "credit_sale":
                d = entry.get("due_date")
                if d:
                    original_amount = max(0, entry.get("amount_paise", 0) - allocations.get(entry["id"], 0))
                    if original_amount == 0:
                        continue
                    inflows.append({
                        "date": d,
                        "amount_paise": original_amount,
                        "source_type": "customer_collection",
                        "source_id": entry["id"],
                        "description": f"{c.get('name', 'Customer')} (Repayment due)",
                    })

    for plan in plans:
        if plan.get("status") == "cancelled":
            continue
        for installment in plan.get("installments", []):
            remaining = installment.get("amount_paise", 0) - installment.get("paid_amount_paise", 0)
            if remaining > 0:
                inflows.append({
                    "date": installment["due_date"],
                    "amount_paise": remaining,
                    "source_type": "repayment_plan",
                    "source_id": installment["id"],
                    "description": f"{plan.get('customer_name', 'Customer')} scheduled instalment (estimate)",
                })

    outflows: List[Dict[str, Any]] = []
    for b in bills:
        remaining = b.get("remaining_amount_paise", 0)
        if remaining > 0 and b.get("status") != "paid":
            d = b.get("due_date")
            if d:
                outflows.append({
                    "date": d,
                    "amount_paise": remaining,
                    "source_type": "supplier_bill",
                    "source_id": b["id"],
                    "description": f"{b.get('supplier_name', 'Supplier')} - {b.get('description', '')}",
                })

    return inflows, outflows
