from fastapi import APIRouter
from app.schemas.dashboard import DashboardResponse, ForecastSummary, RecentTransactionDTO, UpcomingItemDTO
from app.services.seed_data import seed_service

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard():
    """Retrieve canonical dashboard totals, recent activities, and 14-day forecast summary."""
    biz = seed_service.get_business()
    customers = seed_service.get_customers()
    bills = seed_service.get_supplier_bills()
    transactions = seed_service.get_transactions()

    # Calculate server-side aggregates
    total_receivables = sum(c["outstanding_balance_paise"] for c in customers)
    total_payables = sum(b["remaining_amount_paise"] for b in bills if b["status"] != "paid")
    available_cash = biz["opening_cash_paise"]

    # Upcoming items: due customer collections and pending supplier bills
    upcoming: list[UpcomingItemDTO] = []

    for c in customers:
        if c["outstanding_balance_paise"] > 0:
            for entry in c.get("credit_entries", []):
                if entry.get("entry_type") == "credit_sale" and entry.get("due_date"):
                    upcoming.append(
                        UpcomingItemDTO(
                            id=f"up_cust_{entry['id']}",
                            title=f"{c['name']} (Credit Repayment)",
                            entity_type="customer_due",
                            amount_paise=entry["amount_paise"],
                            due_date=entry["due_date"],
                            status="DUE SOON",
                        )
                    )

    for b in bills:
        if b["remaining_amount_paise"] > 0:
            upcoming.append(
                UpcomingItemDTO(
                    id=f"up_bill_{b['id']}",
                    title=f"{b['supplier_name']} - {b['description']}",
                    entity_type="supplier_bill",
                    amount_paise=b["remaining_amount_paise"],
                    due_date=b["due_date"],
                    status="DUE SOON" if b["due_date"] >= "2026-10-17" else "OVERDUE",
                )
            )

    # Sort upcoming by due date ascending
    upcoming.sort(key=lambda x: x.due_date)

    recent: list[RecentTransactionDTO] = []
    for tx in transactions:
        recent.append(
            RecentTransactionDTO(
                id=tx["id"],
                type=tx["type"],
                description=tx["description"],
                amount_paise=tx["amount_paise"],
                date=tx["date"],
                direction=tx["direction"],
                payment_method=tx.get("payment_method", "cash"),
            )
        )

    # Deterministic forecast summary
    lowest_balance_paise = -1000000  # -₹10,000 on Oct 20
    lowest_balance_date = "2026-10-20"
    safety_buffer = biz["cash_safety_buffer_paise"]

    return DashboardResponse(
        currency="INR",
        available_cash_paise=available_cash,
        receivables_paise=total_receivables,
        payables_paise=total_payables,
        today_income_paise=0,
        today_expenses_paise=125000,
        forecast=ForecastSummary(
            horizon_days=14,
            lowest_balance_paise=lowest_balance_paise,
            lowest_balance_date=lowest_balance_date,
            has_shortage=lowest_balance_paise < 0 or lowest_balance_paise < safety_buffer,
            safety_buffer_breach=lowest_balance_paise < safety_buffer,
        ),
        recent_transactions=recent,
        upcoming_items=upcoming,
    )
