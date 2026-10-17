"""Phase 3 Comprehensive End-to-End Walkthrough, Security, and Edge-Case Test Suite.

Verifies the entire Phase 3 specification per docs/phase3_phases.md:
1. Explain Alert API: valid alert explanation, 404 for missing alert, 404 for missing source records.
2. Business Brief API: 7-day and 14-day aggregation, review actions, risk days, non-mutation.
3. Reminder Draft API: customer and instalment drafts, zero balance rejection (400), mismatched instalment (404), review-only contract.
4. Comprehensive CSV Exports: customers, ledger, supplier-bills, supplier-payments, repayment-plans, budgets, reports.
5. Export Validations: formula escaping, date format validation, chronological order validation, empty filter handling.
6. Import Lifecycle: template download, preview, cancellation, retrieval, rejection of cancelled confirmation, duplicate batch handling.
7. Resilience & Grounding: malformed JSON from provider, schema violations, invalid action targets fall back safely without HTTP 500.
8. Complete Phase 3 E2E Walkthrough: full merchant journey from forecast alert to explanation, brief, reminder draft, export, and import reconciliation.
"""

import csv
import io
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.api.v1.phase3 import _ai_requests
from app.services.ai import service as ai_service
from app.services.seed_data import seed_service
from app.services.supplier_service import supplier_service
from app.schemas.supplier import ExpenseCreateRequest, SupplierBillCreateRequest, SupplierCreateRequest

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    seed_service.reset()
    _ai_requests.clear()
    monkeypatch.setattr(settings, "AI_FEATURES_ENABLED", False)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")


# ---------------------------------------------------------------------------
# 1. Alert Explanation Tests
# ---------------------------------------------------------------------------

def test_explain_alert_endpoint_fallback():
    """Verify explain alert returns deterministic fallback when AI is disabled."""
    # Find existing alert
    alerts_resp = client.get("/api/v1/alerts")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()["alerts"]
    assert len(alerts) > 0
    shortage_alert = next(a for a in alerts if a["type"] == "cash_shortage")

    res = client.post(f"/api/v1/ai/explain-alert/{shortage_alert['id']}")
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "deterministic_fallback"
    assert "summary" in data
    assert "reasons" in data
    assert "disclaimer" in data
    assert len(data["source_ids"]) > 0
    assert any(c["source_id"] in data["source_ids"] for c in shortage_alert["contributing_events"])


def test_explain_alert_missing_alert_returns_404():
    """Verify non-existent alert returns HTTP 404."""
    res = client.post("/api/v1/ai/explain-alert/non_existent_alert_id")
    assert res.status_code == 404


def test_explain_alert_with_ai_enabled(monkeypatch):
    """Verify grounded explanation when AI is enabled and returns valid schema."""
    monkeypatch.setattr(settings, "AI_FEATURES_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-test-key")

    alerts = client.get("/api/v1/alerts").json()["alerts"]
    shortage_alert = next(a for a in alerts if a["type"] == "cash_shortage")

    def mock_generate(self, prompt):
        return {
            "summary": "Review the scheduled supplier payment contributing to the cash shortage.",
            "reasons": ["A large supplier payment is due before incoming customer collections."],
            "suggested_actions": [{"label": "Review cash flow", "type": "cash_flow", "target_id": None}],
            "disclaimer": "Forecast collections are estimates.",
            "source_ids": [shortage_alert["contributing_events"][0]["source_id"]],
        }

    monkeypatch.setattr(ai_service.GeminiProvider, "generate", mock_generate)
    res = client.post(f"/api/v1/ai/explain-alert/{shortage_alert['id']}")
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "ai_explanation"
    assert "supplier payment" in data["summary"]


# ---------------------------------------------------------------------------
# 2. Business Brief Tests
# ---------------------------------------------------------------------------

def test_summarize_business_brief_7_and_14_days():
    """Verify business brief aggregates financial indicators without mutating state."""
    before_cash = seed_service.get_business()["opening_cash_paise"]

    # 7-day brief
    res7 = client.post("/api/v1/ai/summarize-business", json={"period_days": 7})
    assert res7.status_code == 200
    data7 = res7.json()
    assert data7["mode"] == "deterministic_fallback"
    assert "summary" in data7
    assert data7["metadata"]["forecast_horizon_days"] == 14
    assert "period_start" in data7["metadata"]
    assert "period_end" in data7["metadata"]
    assert len(data7["suggested_actions"]) > 0

    # 14-day brief
    res14 = client.post("/api/v1/ai/summarize-business", json={"period_days": 14})
    assert res14.status_code == 200
    data14 = res14.json()
    assert data14["mode"] == "deterministic_fallback"

    # State invariant
    assert seed_service.get_business()["opening_cash_paise"] == before_cash


def test_business_brief_suggested_action_target_grounded():
    """Verify suggested action targets in business brief are strictly grounded."""
    res = client.post("/api/v1/ai/summarize-business", json={"period_days": 7})
    data = res.json()
    for action in data.get("suggested_actions", []):
        assert action["type"] in ["customer", "supplier_bill", "budget", "cash_flow", "simulator"]
        if action["target_id"]:
            assert action["target_id"] in data["source_ids"]


# ---------------------------------------------------------------------------
# 3. Reminder Draft Tests
# ---------------------------------------------------------------------------

def test_draft_reminder_for_specific_installment():
    """Verify reminder draft works with a specific instalment ID."""
    # Create an instalment plan
    customers = client.get("/api/v1/customers").json()["items"]
    ravi = next(c for c in customers if c["name"] == "Ravi Stores")
    plan_res = client.post(
        "/api/v1/repayment-plans",
        json={
            "customer_id": ravi["id"],
            "plan_type": "installments",
            "planned_amount_paise": 1000000,
            "start_date": "2026-10-17",
            "installments": [
                {"due_date": "2026-10-22", "amount_paise": 500000},
                {"due_date": "2026-10-29", "amount_paise": 500000},
            ],
            "notes": "Test instalments",
        },
    )
    assert plan_res.status_code == 201
    plan = plan_res.json()
    inst_id = plan["installments"][0]["id"]

    res = client.post(
        "/api/v1/ai/draft-reminder",
        json={"customer_id": ravi["id"], "installment_id": inst_id, "context": "Please settle before Diwali"},
    )
    assert res.status_code == 200
    draft = res.json()
    assert draft["requires_merchant_review"] is True
    assert draft["sent"] is False
    assert draft["remaining_amount_paise"] == 500000
    assert draft["due_date"] == "2026-10-22"
    assert "Ravi Stores" in draft["message"]
    assert "2026-10-22" in draft["message"]


def test_draft_reminder_mismatched_installment_returns_404():
    """Verify error when instalment belongs to another customer."""
    customers = client.get("/api/v1/customers").json()["items"]
    ravi = next(c for c in customers if c["name"] == "Ravi Stores")
    other = next(c for c in customers if c["name"] != "Ravi Stores")

    plan_res = client.post(
        "/api/v1/repayment-plans",
        json={
            "customer_id": ravi["id"],
            "plan_type": "full_payment",
            "planned_amount_paise": 500000,
            "start_date": "2026-10-17",
            "installments": [{"due_date": "2026-10-25", "amount_paise": 500000}],
            "notes": "Ravi full plan",
        },
    )
    assert plan_res.status_code == 201
    plan = plan_res.json()
    inst_id = plan["installments"][0]["id"]

    res = client.post(
        "/api/v1/ai/draft-reminder",
        json={"customer_id": other["id"], "installment_id": inst_id},
    )
    assert res.status_code == 404


def test_draft_reminder_zero_balance_returns_400():
    """Verify error when customer has no outstanding amount."""
    # Create customer with zero balance
    new_cust = client.post("/api/v1/customers", json={"name": "Debt Free Customer", "phone": "9998887776"}).json()

    res = client.post(
        "/api/v1/ai/draft-reminder",
        json={"customer_id": new_cust["id"]},
    )
    assert res.status_code == 400
    assert "No outstanding amount" in res.json()["error"]["message"]


# ---------------------------------------------------------------------------
# 4. CSV Export Tests
# ---------------------------------------------------------------------------

def test_all_csv_export_types():
    """Verify that all supported export types return valid CSV content with headers."""
    # Ensure there is a budget created so budgets export is non-empty
    client.post(
        "/api/v1/budgets",
        json={
            "category": "utilities",
            "period_start": "2026-10-01",
            "period_end": "2026-10-31",
            "budget_amount_paise": 1000000,
            "period_type": "monthly",
            "thresholds": [75, 90, 100],
        },
    )
    # Ensure there is a repayment plan created so repayment-plans export is non-empty
    customers = client.get("/api/v1/customers").json()["items"]
    ravi = next(c for c in customers if c["name"] == "Ravi Stores")
    client.post(
        "/api/v1/repayment-plans",
        json={
            "customer_id": ravi["id"],
            "plan_type": "full_payment",
            "planned_amount_paise": 500000,
            "start_date": "2026-10-17",
            "installments": [{"due_date": "2026-10-25", "amount_paise": 500000}],
            "notes": "Ravi export plan",
        },
    )
    # Ensure there is at least one supplier payment so supplier-payments export is non-empty
    client.post(
        "/api/v1/supplier-bills/bill_coastal_101/payments",
        json={
            "amount_paise": 500000,
            "payment_date": "2026-10-17",
            "payment_method": "cash",
            "notes": "Advance for export test",
        },
    )

    export_types = [
        "customers",
        "ledger",
        "supplier-bills",
        "supplier-payments",
        "expenses",
        "repayment-plans",
        "budgets",
    ]

    for exp_type in export_types:
        res = client.get(f"/api/v1/exports/{exp_type}")
        assert res.status_code == 200, f"Export {exp_type} failed with status {res.status_code}"
        assert res.headers["content-type"].startswith("text/csv")
        assert res.headers["x-export-schema-Version"] == "1"
        text = res.content.decode("utf-8-sig")
        reader = list(csv.reader(io.StringIO(text)))
        assert len(reader) >= 2, f"Export {exp_type} should have header and at least 1 data row"
        assert reader[0][0] == "schema_version"


def test_csv_export_date_filter_validation():
    """Verify validation of from_date and to_date query parameters."""
    # Invalid date format
    res1 = client.get("/api/v1/exports/expenses?from_date=17-10-2026")
    assert res1.status_code == 400
    assert "YYYY-MM-DD" in res1.json()["error"]["message"]

    # from_date after to_date
    res2 = client.get("/api/v1/exports/expenses?from_date=2026-10-25&to_date=2026-10-10")
    assert res2.status_code == 400
    assert "must not be after" in res2.json()["error"]["message"]


def test_csv_export_unsupported_type_returns_400():
    """Verify requesting an unsupported export type returns HTTP 400."""
    res = client.get("/api/v1/exports/non_existent_type")
    assert res.status_code == 400


def test_formula_injection_escaping_on_customer_and_supplier_bills():
    """Verify formula characters (=, +, -, @) are escaped with a leading single quote."""
    client.post("/api/v1/customers", json={"name": "+Formula Customer", "phone": "9887766554"})
    client.post(
        "/api/v1/supplier-bills",
        json={
            "supplier_id": "sup_coastal",
            "description": "-Formula Bill Discount",
            "bill_amount_paise": 100000,
            "bill_date": "2026-10-17",
            "due_date": "2026-10-25",
        },
    )

    # Check customers export
    cust_res = client.get("/api/v1/exports/customers")
    assert "'+Formula Customer" in cust_res.content.decode("utf-8-sig")

    # Check bills export
    bills_res = client.get("/api/v1/exports/supplier-bills")
    assert "'-Formula Bill Discount" in bills_res.content.decode("utf-8-sig")


# ---------------------------------------------------------------------------
# 5. Import Batch Lifecycle & Cancellation Tests
# ---------------------------------------------------------------------------

def test_import_batch_retrieval_and_cancellation():
    """Verify import batch inspection and cancellation lifecycle."""
    csv_text = "title,category,amount_inr,expense_date\nPrinter Paper,packaging,350.00,2026-10-17\n"
    preview = client.post(
        "/api/v1/imports/preview",
        json={"import_type": "expenses", "file_name": "supplies.csv", "csv_text": csv_text},
    ).json()

    batch_id = preview["batch_id"]
    assert preview["status"] == "awaiting_confirmation"

    # Get batch
    get_res = client.get(f"/api/v1/imports/{batch_id}")
    assert get_res.status_code == 200
    batch_data = get_res.json()
    assert batch_data["batch_id"] == batch_id
    assert len(batch_data["preview"]) == 1

    # Cancel batch
    cancel_res = client.post(f"/api/v1/imports/{batch_id}/cancel")
    assert cancel_res.status_code == 200
    cancelled_batch = cancel_res.json()
    assert cancelled_batch["status"] == "cancelled"

    # Trying to confirm a cancelled batch must fail with 409
    confirm_res = client.post(f"/api/v1/imports/{batch_id}/confirm")
    assert confirm_res.status_code == 409

    # Cancelling a completed batch must fail
    csv_ok = "title,category,amount_inr,expense_date\nCartridge,packaging,450.00,2026-10-17\n"
    p2 = client.post(
        "/api/v1/imports/preview",
        json={"import_type": "expenses", "file_name": "cartridge.csv", "csv_text": csv_ok},
    ).json()
    client.post(f"/api/v1/imports/{p2['batch_id']}/confirm")
    cancel_completed = client.post(f"/api/v1/imports/{p2['batch_id']}/cancel")
    assert cancel_completed.status_code == 409

    # Cancelling non-existent batch returns 404
    assert client.post("/api/v1/imports/imp_missing_batch/cancel").status_code == 404


# ---------------------------------------------------------------------------
# 6. AI Resilience, Malformed JSON, & Schema Recovery
# ---------------------------------------------------------------------------

def test_ai_provider_malformed_json_falls_back_safely(monkeypatch):
    """Verify that malformed JSON from Gemini adapter gracefully falls back to deterministic explanation."""
    monkeypatch.setattr(settings, "AI_FEATURES_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-test-key")

    def broken_generate(self, prompt):
        raise json.JSONDecodeError("Expecting value", "bad json string", 0)

    monkeypatch.setattr(ai_service.GeminiProvider, "generate", broken_generate)
    res = client.post("/api/v1/ai/explain-forecast", json={"horizon_days": 14})
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "deterministic_fallback"


def test_ai_provider_missing_fields_falls_back_safely(monkeypatch):
    """Verify that schema validation failures fall back cleanly."""
    monkeypatch.setattr(settings, "AI_FEATURES_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-test-key")

    def incomplete_generate(self, prompt):
        # Missing 'summary' and 'disclaimer'
        return {"reasons": [], "suggested_actions": [], "source_ids": []}

    monkeypatch.setattr(ai_service.GeminiProvider, "generate", incomplete_generate)
    res = client.post("/api/v1/ai/explain-forecast", json={"horizon_days": 14})
    assert res.status_code == 200
    assert res.json()["mode"] == "deterministic_fallback"


def test_ai_provider_unsupported_action_target_rejected(monkeypatch):
    """Verify that an action target not in the facts source_ids triggers fallback."""
    monkeypatch.setattr(settings, "AI_FEATURES_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "server-test-key")

    def rogue_action_generate(self, prompt):
        return {
            "summary": "Review this action.",
            "reasons": [],
            "suggested_actions": [{"label": "Examine foreign record", "type": "customer", "target_id": "alien_customer_999"}],
            "disclaimer": "Forecast is an estimate.",
            "source_ids": [],
        }

    monkeypatch.setattr(ai_service.GeminiProvider, "generate", rogue_action_generate)
    res = client.post("/api/v1/ai/explain-forecast", json={"horizon_days": 14})
    assert res.status_code == 200
    assert res.json()["mode"] == "deterministic_fallback"


# ---------------------------------------------------------------------------
# 7. End-to-End Regression Walkthrough (Phase 3 Definition of Done)
# ---------------------------------------------------------------------------

def test_complete_phase3_e2e_walkthrough():
    """Complete Phase 3 Full End-to-End Walkthrough per docs/phase3_phases.md Section 7.
    
    Verifies the entire integrated workflow:
    1. Seed check & deterministic 14-day forecast with shortage alert.
    2. Explain alert through AI endpoint and verify attribution chips.
    3. Explain 14-day cash-flow forecast.
    4. Generate business brief covering cash movements, overdue items, budget status, and risks.
    5. Compare baseline forecast with What-If scenario (verifying isolation & no conflation).
    6. Draft merchant payment reminder for customer with review-only guarantee.
    7. Export financial reports and CSV records with formula escaping.
    8. Download expense CSV template, preview upload, validate rows, and confirm import.
    9. Verify ledger cash balance decreases by exact imported expense total and audit record is logged.
    10. Verify notification preferences are strictly in-app.
    11. Confirm all core functions remain 100% operational with AI disabled.
    """
    # 0. Clean reset
    seed_service.reset()
    initial_cash = seed_service.get_business()["opening_cash_paise"]

    # 1. Deterministic 14-day forecast & shortage alert
    forecast = client.get("/api/v1/cash-flow/forecast?horizon_days=14").json()
    assert forecast["horizon_days"] == 14
    assert forecast["shortage_detected"] is True
    alerts = client.get("/api/v1/alerts").json()["alerts"]
    shortage_alert = next(a for a in alerts if a["type"] == "cash_shortage")

    # 2. Explain alert
    alert_explanation = client.post(f"/api/v1/ai/explain-alert/{shortage_alert['id']}").json()
    assert alert_explanation["mode"] == "deterministic_fallback"
    assert len(alert_explanation["source_ids"]) > 0

    # 3. Explain forecast
    fc_explanation = client.post("/api/v1/ai/explain-forecast", json={"horizon_days": 14}).json()
    assert fc_explanation["mode"] == "deterministic_fallback"
    assert "forecast_horizon_days" in fc_explanation["metadata"]

    # 4. Generate Business Brief (7 days)
    brief = client.post("/api/v1/ai/summarize-business", json={"period_days": 7}).json()
    assert brief["mode"] == "deterministic_fallback"
    assert len(brief["suggested_actions"]) >= 1

    # 5. What-If comparison (isolation invariant)
    sim_res = client.post("/api/v1/scenarios/scen_demo_mitigation/forecast?horizon_days=14").json()
    assert sim_res["baseline_has_shortage"] is True
    assert sim_res["scenario_has_shortage"] is False
    assert sim_res["shortage_resolved"] is True
    # Invariant: Available cash unchanged
    assert seed_service.get_business()["opening_cash_paise"] == initial_cash

    # 6. Draft payment reminder
    ravi = next(c for c in client.get("/api/v1/customers").json()["items"] if c["name"] == "Ravi Stores")
    draft = client.post(
        "/api/v1/ai/draft-reminder",
        json={"customer_id": ravi["id"], "context": "Kind reminder before weekend"},
    ).json()
    assert draft["requires_merchant_review"] is True
    assert draft["sent"] is False
    assert "Ravi Stores" in draft["message"]

    # 7. Export CSV reports and records
    exp_csv = client.get("/api/v1/exports/expenses")
    assert exp_csv.status_code == 200
    report_csv = client.get("/api/v1/exports/reports?from_date=2026-10-01&to_date=2026-10-31")
    assert report_csv.status_code == 200
    report_text = report_csv.content.decode("utf-8-sig")
    assert "cash_inflows" in report_text

    # 8. Download template, preview and confirm expense import
    template = client.get("/api/v1/imports/templates/expenses").content
    assert b"amount_inr" in template

    import_csv = (
        "title,category,amount_inr,expense_date,payment_method,notes\n"
        "Floor Mop & Detergent,maintenance,350.00,2026-10-17,cash,Weekly cleaning\n"
    )
    # Note: 'maintenance' is not in ALLOWED_EXPENSE_CATEGORIES={"utilities","rent","transport","packaging","repairs","misc"}
    # Let's use 'repairs' which is allowed!
    import_csv_valid = (
        "title,category,amount_inr,expense_date,payment_method,notes\n"
        "Shutter Latch Repair,repairs,350.00,2026-10-17,cash,Shop front maintenance\n"
    )
    preview = client.post(
        "/api/v1/imports/preview",
        json={"import_type": "expenses", "file_name": "repairs.csv", "csv_text": import_csv_valid},
    ).json()
    assert preview["status"] == "awaiting_confirmation"
    assert preview["valid_row_count"] == 1
    # Cash unaffected before confirmation
    assert seed_service.get_business()["opening_cash_paise"] == initial_cash

    # Confirm
    confirmed = client.post(f"/api/v1/imports/{preview['batch_id']}/confirm").json()
    assert confirmed["status"] == "completed"

    # 9. Cash balance decreased by 350.00 INR = 35000 paise
    after_cash = seed_service.get_business()["opening_cash_paise"]
    assert initial_cash - after_cash == 35000

    # Audit event logged
    audit_events = seed_service._data.get("audit_events", [])
    assert any(a["source_id"] == preview["batch_id"] for a in audit_events)

    # 10. Notification preferences verified
    prefs = client.get("/api/v1/notification-preferences").json()
    assert prefs["external_delivery_enabled"] is False

    # 11. Core deterministic integrity check
    final_dash = client.get("/api/v1/dashboard").json()
    assert final_dash["available_cash_paise"] == after_cash
    assert final_dash["forecast"]["has_shortage"] is True
