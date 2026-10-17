# DukaanFlow --- Phase 2 Implementation Plan

**Phase name:** Business Management\
**Prerequisite:** Phase 1 exit criteria are met and the core
ledger-to-forecast-to-simulator flow is stable.\
**Objective:** Extend the MVP with repayment schedules, instalment
tracking, budget alerts, basic reports, and reliable in-app reminders
without compromising financial-data integrity.

## 1. Phase 2 Scope

### Included

1.  Basic customer repayment plans.
2.  Instalment schedules and payment tracking.
3.  Missed-payment and overdue status.
4.  Budget setup and threshold alerts.
5.  Basic financial reports.
6.  Basic in-app reminders for due customer payments and supplier bills.
7.  Integration of repayment schedules and budgets with the existing
    forecast/dashboard where appropriate.

### Not included

-   Lending or loan origination.
-   Automatic payment collection or UPI execution.
-   Real late-fee charging.
-   Automated WhatsApp/SMS delivery unless separately approved and
    integrated.
-   Gemini-powered explanations (Phase 3).
-   Advanced CSV import/export (Phase 3).
-   Full accounting, tax filing, or inventory management.

## 2. Phase 2 Subphases

### Phase 2A --- Repayment Plan Data Model and Rules

**Goal:** Define repayment plans for existing customer credit.

Tasks: - Add a repayment plan entity linked to a customer and, where
applicable, one or more outstanding ledger entries. - Support two plan
types: `full_payment` and `installments`. - Store total planned amount,
start date, final due date, status, and notes. - For instalment plans,
store each instalment's amount, due date, paid amount, and status. -
Define statuses such as `draft`, `active`, `completed`, `overdue`, and
`cancelled`. - Validate that planned amounts do not exceed the eligible
outstanding amount unless an explicit, documented adjustment rule
exists. - Define how a repayment is allocated to a plan and to the
underlying customer balance. - Ensure a plan is a schedule for existing
debt, not a new loan or separate receivable.

**Exit criteria:** - Schema and API models are reviewed. - Plan totals
and remaining balances reconcile with the customer ledger. - Tests cover
invalid amounts, date order, and duplicate allocation.

### Phase 2B --- Instalment Tracking

**Goal:** Let merchants monitor scheduled repayments and record actual
payments.

Tasks: - Create a plan for full payment or instalments. - Generate
instalment rows from merchant-specified amounts/dates. - Show upcoming,
paid, partially paid, missed, and overdue instalments. - Record full or
partial payment against an instalment. - Update plan progress and
remaining balance. - Prevent the same payment from being applied
twice. - Define how a payment exceeding one instalment is handled:
either reject it or explicitly allocate the excess to later
instalments. - Show repayment history and next due date. - Add a clear
distinction between scheduled payments and actual recorded cash
receipts.

**Exit criteria:** - Recording a payment updates the plan and customer
ledger consistently. - Partial payments work without double-counting
cash. - Completed plans cannot receive accidental duplicate payments. -
Dashboard and forecast remain reconciled.

### Phase 2C --- Missed Payments and Overdue Status

**Goal:** Identify repayment schedules that are past due.

Tasks: - Derive overdue status from due date, amount remaining, and
business timezone. - Mark an instalment overdue only if its due date has
passed and its remaining amount is greater than zero. - Show days
overdue and remaining amount. - Provide filters for due today, due soon,
overdue, completed. - Show overdue items on the dashboard and reminder
center. - Allow merchants to mark a schedule as cancelled only with a
reason and audit event. - Do not infer that a customer intentionally
refused payment.

**Exit criteria:** - Status is calculated consistently at the configured
business date. - Paid instalments are never shown as overdue. -
Date-boundary tests pass.

### Phase 2D --- Budget Management

**Goal:** Help merchants monitor recorded spending against their own
limits.

Tasks: - Create monthly budgets by category. - Support a configurable
period and budget amount. - Calculate actual spending from eligible paid
expense records in the period. - Display budget amount, spent amount,
remaining amount, and utilization percentage. - Generate alerts at
configurable thresholds, with defaults of 75%, 90%, and 100%. - Show a
distinct alert when spending exceeds the budget. - Avoid counting
supplier bills twice if inventory expense is represented through another
canonical record. - Explain that budget alerts are based on recorded
expenses and may not reflect unentered spending.

**Exit criteria:** - Budget totals reconcile with expense records. -
Threshold alerts trigger at the correct boundaries. - Editing/reversing
an expense recalculates budget utilization correctly.

### Phase 2E --- Basic Reports

**Goal:** Provide simple, reconcilable summaries of business activity.

Reports: - Income and recorded cash inflows by date range. - Expenses by
category and date range. - Customer receivables and overdue balances. -
Supplier payables and upcoming/overdue bills. - Repayment plan
completion and remaining scheduled amounts. - Budget utilization. -
Cash-flow forecast summary.

Tasks: - Add date range filters and clear report definitions. - Display
totals with Indian currency formatting. - Provide tables and simple
charts. - Show data freshness and date range. - Keep report calculations
server-side. - Clearly distinguish cash movement from credit sales and
outstanding balances.

**Exit criteria:** - Each report total reconciles with source records. -
Empty and partial-data states are understandable. - Date filters and
timezone boundaries are tested.

### Phase 2F --- In-App Reminders

**Goal:** Help merchants notice upcoming obligations without introducing
external messaging dependencies.

Tasks: - Show in-app reminders for customer instalments and supplier
bills due soon. - Show overdue reminders based on current status. - Use
configurable lead times where practical. - Deduplicate reminders by
business, source item, reminder type, and due-date period. - Provide
read/unread or acknowledged state. - Link reminders to the relevant
customer, instalment, or supplier bill. - Avoid sending any external
message automatically. - Ensure reminders do not reveal another
business's data.

**Exit criteria:** - Reminder generation is idempotent. - Acknowledging
a reminder changes only its acknowledgement state. - Reminders link to
the correct source record. - Access control is enforced for all reminder
queries.

### Phase 2G --- Dashboard and Forecast Integration

**Goal:** Make the new management features visible in existing
workflows.

Tasks: - Add next instalments due and overdue plan counts to
dashboard. - Add budget utilization summary. - Include repayment-plan
dates as expected collections in the forecast only where they are not
already represented by the underlying customer collection event. -
Clearly label scheduled repayment dates as estimates, not guaranteed
receipts. - Add quick links from dashboard alerts to relevant records. -
Avoid double-counting a plan and its source ledger entries.

**Exit criteria:** - Dashboard metrics reconcile with underlying
records. - Forecast contains each expected collection/outflow once. -
Changes to plans, payments, expenses, or budgets refresh dependent
views.

### Phase 2H --- Testing, UX Polish, and Release

**Goal:** Deliver a stable Phase 2 increment.

Tasks: - Add loading, empty, error, validation, and success states. -
Test keyboard accessibility and responsive layouts. - Add audit events
for financial mutations and plan cancellation. - Run backend unit/API
tests and frontend tests. - Run an end-to-end scenario covering a plan,
partial instalment, overdue status, budget alert, report, and
reminder. - Update API, schema, app flow, and architecture
documentation. - Verify Phase 1 regression suite remains green.

**Exit criteria:** - All Phase 2 acceptance criteria pass. - No
regression in Phase 1 core workflows. - Demo can be completed from
seeded data without manual database editing.

## 3. Suggested Data Model Additions

### `repayment_plans`

Fields: - `customer_id` - `source_ledger_entry_ids` or a documented
allocation model - `plan_type`: `full_payment` or `installments` -
`planned_amount_paise` - `paid_amount_paise` (derived or reconciled) -
`start_date` - `final_due_date` - `status` - `notes` - `created_by`,
`created_at`, `updated_at`

### `repayment_plans/{planId}/installments`

Fields: - `sequence_number` - `due_date` - `amount_paise` -
`paid_amount_paise` - `status` - `created_at`, `updated_at`

### `budgets`

Fields: - `category` - `period_type` - `period_start` - `period_end` -
`budget_amount_paise` - `thresholds` - `created_by`, `created_at`,
`updated_at`

### `reminders`

Fields: - `reminder_type` - `source_type` - `source_id` - `due_date` -
`status`: `unread`, `read`, `acknowledged` - `dedupe_key` -
`created_at`, `acknowledged_at`

Exact schema details must be reconciled with `03_DATABASE_SCHEMA.md`
before implementation.

## 4. API Additions

Suggested endpoints: - `GET /api/v1/repayment-plans` -
`POST /api/v1/repayment-plans` -
`GET /api/v1/repayment-plans/{plan_id}` -
`PATCH /api/v1/repayment-plans/{plan_id}` -
`POST /api/v1/repayment-plans/{plan_id}/installments/{installment_id}/payments` -
`GET /api/v1/budgets` - `POST /api/v1/budgets` -
`PATCH /api/v1/budgets/{budget_id}` - `GET /api/v1/reports/summary` -
`GET /api/v1/reports/expenses` - `GET /api/v1/reports/receivables` -
`GET /api/v1/reports/payables` - `GET /api/v1/reminders` -
`PATCH /api/v1/reminders/{reminder_id}`

All endpoints require authentication and business-membership
authorization. Validate all linked IDs against the active business.

## 5. Testing Requirements

### Repayment Plans

-   Full-payment plan equals eligible outstanding balance.
-   Instalment amounts sum to planned amount.
-   Dates are valid and ordered.
-   Partial payment updates plan, instalment, customer ledger, and cash
    exactly once.
-   Overpayment follows documented behavior.
-   Completed/cancelled plans cannot accept new payments without an
    explicit reopen flow.

### Budgets

-   75%, 90%, and 100% boundaries are tested.
-   Reversed or edited expenses recalculate totals.
-   Expenses outside the budget period are excluded.
-   Supplier bills are not double-counted as paid expenses.

### Reports

-   Totals reconcile with source records.
-   Date filters honor business timezone.
-   Receivables and cash inflows are not conflated.
-   Empty data and partial data are handled.

### Reminders

-   Duplicate reminder generation is prevented.
-   Acknowledgement is idempotent.
-   Business data isolation is tested.

### Regression

-   All Phase 1 customer, supplier, forecast, alert, and scenario tests
    pass.

## 6. Security and Compliance Boundaries

-   Repayment plans track existing merchant-customer credit only.
-   DukaanFlow does not lend money or originate loans.
-   Do not collect late fees or interest in this phase.
-   Do not initiate payments or ask for UPI PINs, OTPs, bank passwords,
    or card security codes.
-   External reminders require a separately approved provider
    integration and user/merchant consent.
-   Every read/write must enforce business membership and preserve
    financial auditability.

## 7. Definition of Done

-   [ ] Repayment plans support full payment and instalments.
-   [ ] Partial instalment payments update the canonical ledger exactly
    once.
-   [ ] Overdue status is derived correctly.
-   [ ] Budgets calculate utilization and threshold alerts.
-   [ ] Reports reconcile with source records.
-   [ ] In-app reminders are deduplicated and actionable.
-   [ ] Forecast includes scheduled receipts only once and labels
    uncertainty.
-   [ ] Phase 1 regression tests pass.
-   [ ] API/schema/app-flow documentation is updated.
-   [ ] No real lending, late-fee collection, or automatic payment flow
    is introduced.
