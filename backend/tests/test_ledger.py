import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.domain.ledger import calculate_customer_balance, validate_repayment_amount
from app.services.seed_data import seed_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_seed_before_tests():
    seed_service.reset()


def test_calculate_customer_balance():
    entries = [
        {"entry_type": "credit_sale", "amount_paise": 500000, "status": "posted"},
        {"entry_type": "credit_sale", "amount_paise": 250000, "status": "posted"},
        {"entry_type": "repayment", "amount_paise": 300000, "status": "posted"},
    ]
    outstanding, total_credit, total_repaid = calculate_customer_balance(entries)
    assert total_credit == 750000
    assert total_repaid == 300000
    assert outstanding == 450000


def test_validate_repayment():
    # Valid repayment
    validate_repayment_amount(current_outstanding_paise=50000, repayment_amount_paise=25000)

    # Full repayment
    validate_repayment_amount(current_outstanding_paise=50000, repayment_amount_paise=50000)

    # Overpayment rejected
    with pytest.raises(ValueError, match="exceeds current outstanding balance"):
        validate_repayment_amount(current_outstanding_paise=50000, repayment_amount_paise=50001)

    # Zero or negative rejected
    with pytest.raises(ValueError, match="must be greater than zero"):
        validate_repayment_amount(current_outstanding_paise=50000, repayment_amount_paise=0)

    with pytest.raises(ValueError, match="must be greater than zero"):
        validate_repayment_amount(current_outstanding_paise=50000, repayment_amount_paise=-100)


def test_customer_crud_api():
    # Create customer
    res = client.post("/api/v1/customers", json={"name": "Kiran Dairy", "phone": "9988776655", "notes": "Local dairy vendor"})
    assert res.status_code == 201
    cust = res.json()
    assert cust["name"] == "Kiran Dairy"
    assert cust["outstanding_balance_paise"] == 0
    cust_id = cust["id"]

    # Retrieve customer
    res_get = client.get(f"/api/v1/customers/{cust_id}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Kiran Dairy"


def test_ledger_entries_and_cash_sync():
    # 1. Create a customer
    res_create = client.post("/api/v1/customers", json={"name": "Anita Provision", "phone": "9876543219"})
    cust_id = res_create.json()["id"]

    # 2. Add credit sale of ₹10,000 (1000000 paise)
    res_sale = client.post(
        f"/api/v1/customers/{cust_id}/ledger-entries",
        json={
            "entry_type": "credit_sale",
            "amount_paise": 1000000,
            "effective_date": "2026-10-17",
            "due_date": "2026-10-25",
            "notes": "Bulk spices",
        },
    )
    assert res_sale.status_code == 201
    assert res_sale.json()["amount_paise"] == 1000000

    # Verify customer balance is 1000000 paise
    cust = client.get(f"/api/v1/customers/{cust_id}").json()
    assert cust["outstanding_balance_paise"] == 1000000
    assert cust["total_credit_paise"] == 1000000
    assert cust["total_repaid_paise"] == 0

    # 3. Check initial dashboard available cash
    dash_before = client.get("/api/v1/dashboard").json()
    initial_cash = dash_before["available_cash_paise"]

    # 4. Attempt overpayment of ₹12,000 (1200000 paise) -> Must fail with 400
    res_overpay = client.post(
        f"/api/v1/customers/{cust_id}/ledger-entries",
        json={
            "entry_type": "repayment",
            "amount_paise": 1200000,
            "effective_date": "2026-10-18",
            "payment_method": "cash",
            "notes": "Overpayment attempt",
        },
    )
    assert res_overpay.status_code == 400
    assert "exceeds current outstanding balance" in res_overpay.json()["error"]["message"]

    # 5. Record valid partial repayment of ₹4,000 (400000 paise)
    res_repay = client.post(
        f"/api/v1/customers/{cust_id}/ledger-entries",
        json={
            "entry_type": "repayment",
            "amount_paise": 400000,
            "effective_date": "2026-10-18",
            "payment_method": "cash",
            "notes": "Partial cash payment",
        },
    )
    assert res_repay.status_code == 201

    # 6. Verify customer balance updated: 10,000 - 4,000 = 6,000 (600000 paise)
    cust_after = client.get(f"/api/v1/customers/{cust_id}").json()
    assert cust_after["outstanding_balance_paise"] == 600000
    assert cust_after["total_repaid_paise"] == 400000

    # 7. Verify cash synchronization: dashboard available cash increased by 400000 paise
    dash_after = client.get("/api/v1/dashboard").json()
    assert dash_after["available_cash_paise"] == initial_cash + 400000

    # 8. Verify ledger history endpoint returns both entries
    res_ledger = client.get(f"/api/v1/customers/{cust_id}/ledger")
    assert res_ledger.status_code == 200
    ledger_data = res_ledger.json()
    assert len(ledger_data["entries"]) == 2
    assert ledger_data["customer"]["outstanding_balance_paise"] == 600000
