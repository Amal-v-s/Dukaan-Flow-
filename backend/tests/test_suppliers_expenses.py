import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.seed_data import seed_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_seed():
    seed_service.reset()


def test_supplier_crud():
    res = client.post("/api/v1/suppliers", json={"name": "Patanjali Wholesale", "phone": "9900112233"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Patanjali Wholesale"
    assert "id" in data

    res_list = client.get("/api/v1/suppliers")
    assert res_list.status_code == 200
    assert any(s["name"] == "Patanjali Wholesale" for s in res_list.json()["items"])


def test_supplier_bill_and_payment_flow():
    # 1. Register a supplier
    res_sup = client.post("/api/v1/suppliers", json={"name": "Kaveri Beverages"})
    sup_id = res_sup.json()["id"]

    # 2. Check initial cash
    dash_before = client.get("/api/v1/dashboard").json()
    initial_cash = dash_before["available_cash_paise"]

    # 3. Create a bill for ₹15,000 (1500000 paise)
    res_bill = client.post(
        "/api/v1/supplier-bills",
        json={
            "supplier_id": sup_id,
            "description": "Cold drinks and juices crate stock",
            "bill_amount_paise": 1500000,
            "bill_date": "2026-10-17",
            "due_date": "2026-10-23",
        },
    )
    assert res_bill.status_code == 201
    bill = res_bill.json()
    bill_id = bill["id"]
    assert bill["remaining_amount_paise"] == 1500000
    assert bill["status"] == "unpaid"

    # 4. Verify unpaid bill does NOT decrease cash
    dash_unpaid = client.get("/api/v1/dashboard").json()
    assert dash_unpaid["available_cash_paise"] == initial_cash

    # 5. Overpayment attempt: paying ₹16,000 on ₹15,000 bill -> must fail with 400
    res_overpay = client.post(
        f"/api/v1/supplier-bills/{bill_id}/payments",
        json={"amount_paise": 1600000, "payment_date": "2026-10-18", "payment_method": "cash"},
    )
    assert res_overpay.status_code == 400
    assert "exceeds remaining bill due" in res_overpay.json()["error"]["message"]

    # 6. Valid partial payment of ₹5,000 (500000 paise)
    res_pay = client.post(
        f"/api/v1/supplier-bills/{bill_id}/payments",
        json={"amount_paise": 500000, "payment_date": "2026-10-18", "payment_method": "cash"},
    )
    assert res_pay.status_code == 201

    # Check bill status is now partially_paid
    bills_after = client.get(f"/api/v1/supplier-bills").json()["items"]
    updated_bill = next(b for b in bills_after if b["id"] == bill_id)
    assert updated_bill["paid_amount_paise"] == 500000
    assert updated_bill["remaining_amount_paise"] == 1000000
    assert updated_bill["status"] == "partially_paid"

    # Verify cash decreased by 500000 paise
    dash_partial = client.get("/api/v1/dashboard").json()
    assert dash_partial["available_cash_paise"] == initial_cash - 500000

    # 7. Settle remaining ₹10,000 (1000000 paise)
    res_settle = client.post(
        f"/api/v1/supplier-bills/{bill_id}/payments",
        json={"amount_paise": 1000000, "payment_date": "2026-10-19", "payment_method": "upi"},
    )
    assert res_settle.status_code == 201

    bills_final = client.get(f"/api/v1/supplier-bills").json()["items"]
    final_bill = next(b for b in bills_final if b["id"] == bill_id)
    assert final_bill["remaining_amount_paise"] == 0
    assert final_bill["status"] == "paid"


def test_expense_creation_and_cash_sync():
    dash_before = client.get("/api/v1/dashboard").json()
    initial_cash = dash_before["available_cash_paise"]

    # Create shop expense of ₹2,000 (200000 paise) for packaging
    res = client.post(
        "/api/v1/expenses",
        json={
            "title": "Carry bags and packing tape",
            "category": "packaging",
            "amount_paise": 200000,
            "expense_date": "2026-10-17",
            "payment_method": "cash",
        },
    )
    assert res.status_code == 201
    expense = res.json()
    assert expense["category"] == "packaging"
    assert expense["amount_paise"] == 200000

    # Verify cash decreased by 200000 paise
    dash_after = client.get("/api/v1/dashboard").json()
    assert dash_after["available_cash_paise"] == initial_cash - 200000

    # Verify expense appears in transactions endpoint
    txs = client.get("/api/v1/transactions").json()["items"]
    assert any(t["description"] == "Carry bags and packing tape" and t["direction"] == "outflow" for t in txs)
