# DukaanFlow --- Database Schema

## 1. Design Principles

-   Firestore is the recommended MVP database.
-   Use document IDs as opaque identifiers; do not expose sequential
    IDs.
-   Store monetary amounts as integer paise (`amount_paise`) to avoid
    floating-point errors.
-   Store timestamps in UTC; represent business due dates as ISO date
    strings (`YYYY-MM-DD`) interpreted in `Asia/Kolkata` unless the
    business timezone is configured.
-   Every business-owned document must carry `business_id` or be stored
    beneath a business-scoped path.
-   Every query must enforce business scope on the server.
-   Prefer append-only ledger events for money movements; use
    reversals/corrections rather than silently deleting financial
    history.

## 2. Suggested Firestore Collections

### `businesses/{businessId}`

``` json
{
  "name": "Demo Kirana Store",
  "currency": "INR",
  "timezone": "Asia/Kolkata",
  "opening_cash_paise": 1500000,
  "cash_safety_buffer_paise": 1500000,
  "is_demo": true,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### `businesses/{businessId}/members/{userId}`

``` json
{
  "role": "owner",
  "status": "active",
  "created_at": "timestamp"
}
```

### `businesses/{businessId}/customers/{customerId}`

``` json
{
  "name": "Ravi Stores",
  "phone": null,
  "notes": "",
  "is_active": true,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### `businesses/{businessId}/customer_ledger_entries/{entryId}`

``` json
{
  "customer_id": "customer_123",
  "entry_type": "credit_sale",
  "amount_paise": 500000,
  "effective_date": "2026-10-17",
  "due_date": "2026-10-20",
  "status": "posted",
  "reference": null,
  "notes": "Inventory sold on credit",
  "created_by": "user_123",
  "created_at": "timestamp",
  "reversal_of": null
}
```

Allowed entry types: `credit_sale`, `repayment`, `adjustment`,
`reversal`. Repayment entries must reference the customer and must not
exceed the outstanding balance unless a documented customer-credit rule
is added.

### `businesses/{businessId}/suppliers/{supplierId}`

``` json
{
  "name": "Coastal Wholesale",
  "phone": null,
  "notes": "",
  "is_active": true,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### `businesses/{businessId}/supplier_bills/{billId}`

``` json
{
  "supplier_id": "supplier_123",
  "description": "Stock purchase",
  "bill_amount_paise": 2500000,
  "paid_amount_paise": 0,
  "bill_date": "2026-10-17",
  "due_date": "2026-10-20",
  "status": "unpaid",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

Status values: `unpaid`, `partially_paid`, `paid`, `voided`.

### `businesses/{businessId}/supplier_payments/{paymentId}`

``` json
{
  "supplier_id": "supplier_123",
  "bill_id": "bill_123",
  "amount_paise": 500000,
  "payment_date": "2026-10-18",
  "payment_method": "cash",
  "created_by": "user_123",
  "created_at": "timestamp",
  "reversal_of": null
}
```

### `businesses/{businessId}/expenses/{expenseId}`

``` json
{
  "title": "Electricity",
  "category": "utilities",
  "amount_paise": 125000,
  "expense_date": "2026-10-17",
  "payment_status": "paid",
  "due_date": null,
  "payment_method": "cash",
  "notes": "",
  "created_by": "user_123",
  "created_at": "timestamp",
  "reversal_of": null
}
```

### `businesses/{businessId}/cash_events/{eventId}`

``` json
{
  "event_type": "opening_balance",
  "amount_paise": 1500000,
  "direction": "inflow",
  "effective_date": "2026-10-17",
  "source_type": "business",
  "source_id": null,
  "status": "posted",
  "created_by": "user_123",
  "created_at": "timestamp"
}
```

Cash events are the normalized source for actual cash movements. Avoid
duplicating a customer repayment, supplier payment, or paid expense into
cash events unless the service uses a single transaction/batch to keep
both records consistent.

### `businesses/{businessId}/scenarios/{scenarioId}`

``` json
{
  "name": "Collect Ravi payment earlier",
  "description": "",
  "created_by": "user_123",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### `businesses/{businessId}/scenarios/{scenarioId}/events/{eventId}`

``` json
{
  "event_type": "customer_collection",
  "amount_paise": 1200000,
  "original_date": "2026-10-22",
  "scenario_date": "2026-10-19",
  "source_type": "customer_ledger_entry",
  "source_id": "entry_123"
}
```

### `businesses/{businessId}/audit_events/{auditId}`

``` json
{
  "actor_user_id": "user_123",
  "action": "customer_repayment.created",
  "entity_type": "customer_ledger_entry",
  "entity_id": "entry_123",
  "occurred_at": "timestamp",
  "request_id": "req_123",
  "metadata": {}
}
```

## 3. Derived Values

-   Customer outstanding = valid posted credit sales + debit adjustments
    − valid repayments − credit adjustments.
-   Supplier outstanding = bill amount − valid supplier payments.
-   Actual available cash = opening cash + posted cash inflows − posted
    cash outflows.
-   Forecast balance = actual available cash at forecast start + future
    forecast inflows − future forecast outflows.
-   Dashboard totals must be calculated server-side from canonical
    records or maintained aggregates that are transactionally updated
    and reconcilable.

## 4. Indexes

Likely composite indexes: - Customer ledger entries:
`customer_id + effective_date desc` - Customer ledger entries:
`due_date + status` - Supplier bills: `status + due_date` - Expenses:
`expense_date desc + category` - Cash events:
`effective_date asc + status` - Audit events: `occurred_at desc` -
Scenario events: `source_type + source_id`

Confirm actual indexes from Firestore query errors and commit index
configuration to source control.

## 5. Consistency Rules

-   Use Firestore transactions/batched writes for logically coupled
    records.
-   Validate that related customer, supplier, bill, and scenario IDs
    belong to the same business.
-   Never let client-provided `business_id` alone authorize access.
-   Do not physically delete posted financial events in normal flows;
    reverse them and retain audit metadata.
-   Ensure a payment cannot exceed the outstanding bill or customer
    balance unless an explicit credit policy is defined.

## 6. Firestore Runtime Collections

The backend uses the Admin/server Firestore SDK with Application Default Credentials. All business records are stored beneath `businesses/{businessId}`; request scope is derived from the verified JWT user record. The compatibility service layer currently maps customers, suppliers, supplier bills, repayment plans, budgets, scenarios, reminders, audit events, AI metadata, and import batches to tenant subcollections. Cashbook transactions use the `cash_events` subcollection. Notification preferences use `businesses/{businessId}/settings/notification_preferences`.

User credentials are stored only on the server in `users/{userId}` with a bcrypt password hash. `user_email_index/{sha256(normalizedEmail)}` provides unique email lookup, and `businesses/{businessId}/members/{userId}` records active membership. The browser Firebase web configuration is not used for privileged database access.

AI logs contain request ID, use case, result status, provider, and latency only. They do not retain prompts or model responses. Import batches retain normalized rows only until completion/cancellation; the raw CSV is never stored. Confirmed expense rows retain import batch/row provenance. Configured authenticated requests stage Firestore changes in a batched write and commit them before completing the request. Account/business/member registration uses a Firestore transaction.

When `GOOGLE_CLOUD_PROJECT` and Firestore credentials are configured, failure to load or initialize the Firestore SDK is fatal rather than silently switching to volatile memory. Without a project configured, isolated local tests use the in-memory adapter. The Firestore emulator can be selected with `FIRESTORE_EMULATOR_HOST`.

**Current compatibility model:** Existing service APIs still consume customer records containing `credit_entries`, supplier bills containing their `payments`, and repayment plans containing their installments. Those child records are currently embedded in their parent documents to preserve current service behavior; `transactions` are stored in `cash_events`. The normalized `customer_ledger_entries` and `supplier_payments` collections above remain the target for a later data-model normalization pass. Keep these arrays below Firestore's document size limit.
