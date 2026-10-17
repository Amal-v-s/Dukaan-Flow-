# DukaanFlow --- API Specification

**Base path:** `/api/v1`\
**Format:** JSON\
**Money:** integer paise (`amount_paise`)\
**Dates:** ISO 8601 timestamps or `YYYY-MM-DD` business dates\
**Authentication:** verified bearer/session identity; all routes require
business membership except health endpoints and explicitly configured
demo bootstrap routes.

## 1. Conventions

-   Responses use JSON.
-   List endpoints should support `limit` and `cursor` or another
    documented pagination scheme.
-   Mutating requests should validate a request body and return
    created/updated resources.
-   Include a request ID in responses/logs.
-   Standard error shape:

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request could not be validated.",
    "request_id": "req_example",
    "details": []
  }
}
```

-   Never return internal stack traces or secret values.

## 2. Health

### `GET /health/live`

Returns process liveness.

### `GET /health/ready`

Checks required dependencies such as Firestore availability.

## 3. Dashboard

### `GET /api/v1/dashboard`

Returns dashboard totals, recent transactions, upcoming obligations, and
forecast summary. Example response:

``` json
{
  "currency": "INR",
  "available_cash_paise": 1500000,
  "receivables_paise": 5000000,
  "payables_paise": 2500000,
  "today_income_paise": 0,
  "today_expenses_paise": 0,
  "forecast": {
    "horizon_days": 14,
    "lowest_balance_paise": 0,
    "lowest_balance_date": "2026-10-20",
    "has_shortage": true
  },
  "recent_transactions": [],
  "upcoming_items": []
}
```

## 4. Customers and Ledger

-   `GET /api/v1/customers?query=&limit=&cursor=`
-   `POST /api/v1/customers`
-   `GET /api/v1/customers/{customer_id}`
-   `PATCH /api/v1/customers/{customer_id}`
-   `GET /api/v1/customers/{customer_id}/ledger`
-   `POST /api/v1/customers/{customer_id}/ledger-entries`

Credit sale request:

``` json
{
  "entry_type": "credit_sale",
  "amount_paise": 500000,
  "effective_date": "2026-10-17",
  "due_date": "2026-10-20",
  "notes": "Stock sold on credit"
}
```

Repayment request:

``` json
{
  "entry_type": "repayment",
  "amount_paise": 200000,
  "effective_date": "2026-10-18",
  "payment_method": "cash",
  "notes": "Partial repayment"
}
```

The service calculates outstanding balance and rejects invalid
overpayment by default.

## 5. Suppliers and Bills

-   `GET /api/v1/suppliers`
-   `POST /api/v1/suppliers`
-   `GET /api/v1/suppliers/{supplier_id}`
-   `PATCH /api/v1/suppliers/{supplier_id}`
-   `GET /api/v1/supplier-bills?status=&due_before=`
-   `POST /api/v1/supplier-bills`
-   `GET /api/v1/supplier-bills/{bill_id}`
-   `POST /api/v1/supplier-bills/{bill_id}/payments`

Bill request:

``` json
{
  "supplier_id": "supplier_123",
  "description": "Stock purchase",
  "bill_amount_paise": 2500000,
  "bill_date": "2026-10-17",
  "due_date": "2026-10-20"
}
```

Supplier payment request:

``` json
{
  "amount_paise": 500000,
  "payment_date": "2026-10-18",
  "payment_method": "cash"
}
```

## 6. Expenses and Transactions

-   `GET /api/v1/expenses?from=&to=&category=`
-   `POST /api/v1/expenses`
-   `PATCH /api/v1/expenses/{expense_id}` for allowed editable fields
-   `POST /api/v1/expenses/{expense_id}/reversals`
-   `GET /api/v1/transactions?from=&to=&type=&limit=&cursor=`

Expense request:

``` json
{
  "title": "Electricity",
  "category": "utilities",
  "amount_paise": 125000,
  "expense_date": "2026-10-17",
  "payment_status": "paid",
  "due_date": null,
  "payment_method": "cash"
}
```

## 7. Cash Flow

### `GET /api/v1/cash-flow/forecast?horizon_days=14`

Returns daily projected closing balances and contributing events.
Example:

``` json
{
  "currency": "INR",
  "horizon_days": 14,
  "cash_safety_buffer_paise": 1500000,
  "days": [
    {
      "date": "2026-10-18",
      "opening_balance_paise": 1500000,
      "inflows_paise": 0,
      "outflows_paise": 2500000,
      "closing_balance_paise": -1000000,
      "below_zero": true,
      "below_safety_buffer": true,
      "contributors": [
        {"source_type": "supplier_bill", "source_id": "bill_123", "amount_paise": 2500000}
      ]
    }
  ],
  "assumptions": ["Expected collections are estimates, not guaranteed."]
}
```

## 8. Alerts

-   `GET /api/v1/alerts`
-   `PATCH /api/v1/alerts/{alert_id}` only if alert acknowledgement
    state is persisted. Alert generation should be derived from forecast
    and configured thresholds. Do not create duplicate persistent alerts
    on every recalculation without a deduplication rule.

## 9. What-If Simulator

-   `GET /api/v1/scenarios/options?horizon_days=14` returns eligible
    collections and supplier bills in the current business forecast
    window.
-   `POST /api/v1/scenarios/preview?horizon_days=14` previews one event
    change or hypothetical expense without saving a scenario.
-   `POST /api/v1/scenarios`
-   `GET /api/v1/scenarios`
-   `GET /api/v1/scenarios/{scenario_id}`
-   `POST /api/v1/scenarios/{scenario_id}/events`
-   `POST /api/v1/scenarios/{scenario_id}/forecast`
-   `DELETE /api/v1/scenarios/{scenario_id}` for draft scenarios only,
    if deletion is enabled.

Preview request example:

``` json
{
  "event_type": "customer_collection",
  "source_id": "entry_123",
  "amount_paise": 1200000,
  "original_date": "2026-10-22",
  "scenario_date": "2026-10-19"
}
```

For an unexpected expense, use `event_type: "extra_expense"` and omit
`source_id` and `original_date`. Preview dates must fall within the
requested forecast window.

Forecast response should contain baseline and scenario series, delta at
each date, lowest balance/date, and shortage status. Scenario changes
must never mutate ledger records.

## 10. Phase 2+ Endpoints

-   `GET/POST /api/v1/repayment-plans`
-   `GET/PATCH /api/v1/repayment-plans/{plan_id}`
-   `GET/POST /api/v1/budgets`
-   `GET /api/v1/reports/summary`
-   CSV import/export routes only after validation and file-safety
    requirements are implemented.
-   AI explanation endpoint only in Phase 3 and must consume
    server-calculated facts.

## Phase 2 Demo Endpoints

- `GET/POST /api/v1/repayment-plans`
- `GET /api/v1/repayment-plans/{plan_id}`
- `POST /api/v1/repayment-plans/{plan_id}/installments/{installment_id}/payments`
- `PATCH /api/v1/repayment-plans/{plan_id}/cancel` (reason required)
- `GET/POST /api/v1/budgets`, `PATCH /api/v1/budgets/{budget_id}`
- `GET /api/v1/reports/summary?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- `GET /api/v1/reminders`, `PATCH /api/v1/reminders/{reminder_id}` (`read` or `acknowledged`)

These Phase 2 endpoints currently use the process-local demo store. Repayment-plan dates are estimates; the payment endpoint records actual cash and ledger changes. Authentication and tenant isolation are not implemented in this demo, so do not use it for production data.

## 11. Status Codes

-   `200`: successful read/update
-   `201`: created
-   `204`: successful deletion where allowed
-   `400`: invalid business operation
-   `401`: unauthenticated
-   `403` or consistent `404`: unauthorized resource access
-   `404`: resource not found
-   `409`: conflicting state or idempotency conflict
-   `422`: schema validation failure
-   `429`: rate limit exceeded
-   `500`: generic unexpected failure

## Phase 3 Demo Endpoints

AI assistance: `POST /api/v1/ai/explain-forecast`, `POST /api/v1/ai/explain-alert/{alert_id}`, `POST /api/v1/ai/summarize-business`, and `POST /api/v1/ai/draft-reminder`.

CSV exports: `GET /api/v1/exports/{customers|ledger|supplier-bills|supplier-payments|expenses|repayment-plans|budgets|reports}`. Date filters are `from_date` and `to_date`; report export requires both.

Expense import: `GET /api/v1/imports/templates/expenses`, `POST /api/v1/imports/preview`, `GET /api/v1/imports/{batch_id}`, `POST /api/v1/imports/{batch_id}/confirm`, and `POST /api/v1/imports/{batch_id}/cancel`. Import requests carry UTF-8 CSV text in a JSON body, limited to one megabyte and 400 rows so each confirmation fits within an atomic Firestore write batch.

Notification preferences: `GET/PATCH /api/v1/notification-preferences`. External delivery is disabled. Phase 3 routes use the existing in-memory single-business demo store; authentication and tenant membership enforcement remain unimplemented and are required before production use.
