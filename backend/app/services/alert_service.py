"""Alert generation service derived deterministically from 14-day cash-flow forecast.

RULES:
- Alert generation must be derived from forecast and configured thresholds.
- Do not create duplicate persistent alerts on every recalculation without a deduplication rule.
- No LLM/AI math: severity and breach amounts are computed strictly in Python integer paise.
- Explain date, threshold, and contributing bills/collections.
"""

from datetime import date
from typing import Dict, List, Set
from app.domain.forecast import generate_forecast
from app.domain.money import format_paise_to_inr
from app.schemas.alert import AlertContributorDTO, CashAlertDTO, AlertsListResponse
from app.services.seed_data import seed_service


class AlertService:
    def __init__(self):
        self._acknowledged_ids: Set[str] = set()

    def acknowledge_alert(self, alert_id: str, acknowledged: bool = True) -> bool:
        if acknowledged:
            self._acknowledged_ids.add(alert_id)
        else:
            self._acknowledged_ids.discard(alert_id)
        return True

    def reset_acknowledgements(self) -> None:
        self._acknowledged_ids.clear()

    def get_alerts(self, include_acknowledged: bool = False) -> AlertsListResponse:
        biz = seed_service.get_business()
        customers = seed_service.get_customers()
        bills = seed_service.get_supplier_bills()

        start_date = date.fromisoformat("2026-10-17")
        safety_buffer = biz.get("cash_safety_buffer_paise", 1500000)

        # Inflows
        inflows = []
        for c in customers:
            for entry in c.get("credit_entries", []):
                if entry.get("status", "posted") == "posted" and entry.get("entry_type") == "credit_sale":
                    d = entry.get("due_date")
                    if d:
                        inflows.append({
                            "date": d,
                            "amount_paise": entry["amount_paise"],
                            "source_type": "customer_collection",
                            "source_id": entry["id"],
                            "description": f"{c['name']} (Repayment due)",
                        })

        # Outflows
        outflows = []
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
                        "description": f"{b['supplier_name']} - {b['description']}",
                    })

        forecast = generate_forecast(
            start_date=start_date,
            opening_cash_paise=biz["opening_cash_paise"],
            inflows=inflows,
            outflows=outflows,
            safety_buffer_paise=safety_buffer,
            horizon_days=14,
        )

        alerts: List[CashAlertDTO] = []

        # 1. Critical Cash Deficit Alerts (closing < 0)
        deficit_days = [d for d in forecast.days if d.below_zero]
        if deficit_days:
            # Group or take the most severe deficit
            worst_day = min(deficit_days, key=lambda d: d.closing_balance_paise)
            alert_id = f"alert_deficit_{worst_day.date}"
            
            # Identify contributing events
            contributors: List[AlertContributorDTO] = []
            for c in worst_day.contributors:
                contributors.append(
                    AlertContributorDTO(
                        source_type=c.source_type,
                        source_id=c.source_id,
                        description=c.description,
                        amount_paise=c.amount_paise,
                        direction="outflow" if "bill" in c.source_type or "expense" in c.source_type else "inflow",
                    )
                )

            # Look for upcoming collections that could bridge this gap
            later_inflows = [
                m for m in inflows if m["date"] > worst_day.date
            ]
            advice_parts = []
            if contributors:
                outflow_contribs = [c for c in contributors if c.direction == "outflow"]
                if outflow_contribs:
                    advice_parts.append(f"Negotiate delaying {outflow_contribs[0].description}")
            if later_inflows:
                advice_parts.append(f"Collect {later_inflows[0]['description']} earlier")
            suggested_action = " or ".join(advice_parts) if advice_parts else "Review upcoming cash commitments."

            deficit_amount = abs(worst_day.closing_balance_paise)
            alerts.append(
                CashAlertDTO(
                    id=alert_id,
                    type="cash_shortage",
                    severity="critical",
                    title=f"Projected Cash Deficit ({format_paise_to_inr(worst_day.closing_balance_paise)} on {worst_day.date})",
                    message=(
                        f"Projected cash drops below zero to {format_paise_to_inr(worst_day.closing_balance_paise)} "
                        f"on {worst_day.date}. Net shortfall is {format_paise_to_inr(deficit_amount)}."
                    ),
                    breach_date=worst_day.date,
                    projected_balance_paise=worst_day.closing_balance_paise,
                    threshold_paise=0,
                    deficit_paise=deficit_amount,
                    acknowledged=alert_id in self._acknowledged_ids,
                    contributing_events=contributors,
                    suggested_action=suggested_action,
                    created_at="2026-10-17T00:00:00Z",
                )
            )

        # 2. Safety Buffer Breach Alerts (0 <= closing < safety_buffer)
        buffer_days = [d for d in forecast.days if not d.below_zero and d.below_safety_buffer]
        if buffer_days and safety_buffer > 0:
            first_buffer_day = buffer_days[0]
            alert_id = f"alert_buffer_{first_buffer_day.date}"
            buffer_deficit = safety_buffer - first_buffer_day.closing_balance_paise
            
            contributors = [
                AlertContributorDTO(
                    source_type=c.source_type,
                    source_id=c.source_id,
                    description=c.description,
                    amount_paise=c.amount_paise,
                    direction="outflow" if "bill" in c.source_type or "expense" in c.source_type else "inflow",
                )
                for c in first_buffer_day.contributors
            ]

            alerts.append(
                CashAlertDTO(
                    id=alert_id,
                    type="safety_buffer_breach",
                    severity="warning",
                    title=f"Safety Buffer Breach ({format_paise_to_inr(first_buffer_day.closing_balance_paise)} on {first_buffer_day.date})",
                    message=(
                        f"Available cash drops to {format_paise_to_inr(first_buffer_day.closing_balance_paise)} on "
                        f"{first_buffer_day.date}, which is below your safety threshold of {format_paise_to_inr(safety_buffer)}."
                    ),
                    breach_date=first_buffer_day.date,
                    projected_balance_paise=first_buffer_day.closing_balance_paise,
                    threshold_paise=safety_buffer,
                    deficit_paise=buffer_deficit,
                    acknowledged=alert_id in self._acknowledged_ids,
                    contributing_events=contributors,
                    suggested_action="Maintain minimum working buffer for unexpected shop operating expenses.",
                    created_at="2026-10-17T00:00:00Z",
                )
            )

        # Filter out acknowledged if not requested
        visible_alerts = alerts if include_acknowledged else [a for a in alerts if not a.acknowledged]

        return AlertsListResponse(
            active_count=len(visible_alerts),
            critical_count=sum(1 for a in visible_alerts if a.severity == "critical"),
            warning_count=sum(1 for a in visible_alerts if a.severity == "warning"),
            alerts=visible_alerts,
        )


alert_service = AlertService()
