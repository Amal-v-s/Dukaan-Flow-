# DukaanFlow --- Product Requirements Document (PRD)

**Status:** Phase 1 MVP specification\
**Product:** DukaanFlow\
**Tagline:** Track Every Rupee. Plan Every Move.\
**Primary market:** Indian small merchants, kirana stores, and local
wholesalers\
**Currency:** INR (₹)

## 1. Product Summary

DukaanFlow combines a digital customer-credit ledger, supplier payable
tracking, expense records, deterministic 14-day cash-flow forecasting,
shortage alerts, and a What-If Simulator. The MVP helps merchants
understand available cash, money owed to them, money they owe, and how
upcoming transactions may affect liquidity.

## 2. Problem

Small merchants commonly track customer credit, repayments, supplier
bills, and expenses in separate notebooks or tools. Outstanding
receivables can be mistaken for available cash, while supplier bills and
rent create time-sensitive obligations. Existing records often show what
happened but do not make future cash pressure easy to understand.

## 3. Goals

-   Provide one place to record and inspect customer dues, repayments,
    supplier bills, and expenses.
-   Clearly separate actual cash from receivables, payables, and
    expected future movements.
-   Calculate a deterministic, explainable 14-day cash forecast.
-   Warn about projected negative cash or balances below a
    merchant-configured safety buffer.
-   Let merchants test hypothetical changes without altering real ledger
    records.
-   Deliver a polished desktop-first demo with realistic sample data and
    responsive behavior.

## 4. Non-Goals for Phase 1

-   Direct bank-account aggregation or automatic transaction ingestion.
-   UPI payment execution, lending, credit underwriting, or loan
    origination.
-   Collecting real late fees or interest.
-   Automated WhatsApp/SMS delivery unless a separately approved
    provider integration is added.
-   AI-generated financial calculations.
-   Multi-branch accounting, tax filing, GST filing, inventory
    management, payroll, or full double-entry accounting.
-   Production-grade multi-tenant onboarding beyond the security
    foundation required by the implementation.

## 5. Target Users

### Primary: Merchant / Shop Owner

Needs to know how much cash is available, which customers owe money,
which supplier bills are due, and whether cash may run short.

### Secondary: Bookkeeping Helper

May enter transactions and reconcile balances on behalf of a merchant.
Any future role-based access must be explicit and server-enforced.

## 6. Core User Stories and Acceptance Criteria

### Dashboard

-   As a merchant, I can see available cash, customer receivables,
    supplier payables, recent transactions, upcoming obligations, and a
    14-day forecast.
-   Acceptance: KPI totals are derived from persisted ledger data;
    sample data is clearly labeled; receivables are not counted as cash
    before collection.

### Customer Ledger

-   As a merchant, I can create customers, record credit sales, and
    record full or partial repayments.
-   Acceptance: outstanding balance equals credit charges minus valid
    repayments; overpayment is rejected or explicitly handled by a
    documented credit-balance rule; all amounts use integer paise or
    integer INR consistently.

### Supplier Bills and Expenses

-   As a merchant, I can record bills, due dates, partial payments, and
    paid expenses.
-   Acceptance: unpaid bills remain liabilities; cash decreases only
    when a payment is recorded; due dates feed the forecast.

### Forecast

-   As a merchant, I can view projected balances for today through the
    next 14 days.
-   Acceptance: the same input ledger always produces the same forecast;
    every included inflow/outflow has a traceable source; uncertain
    collections are labeled as estimates.

### Shortage Alerts

-   As a merchant, I can see when projected cash breaches zero or the
    configured safety buffer and understand why.
-   Acceptance: alert includes date, projected balance, threshold
    breached, and relevant contributing items; no unsupported claim that
    an expected customer payment is guaranteed.

### What-If Simulator

-   As a merchant, I can alter selected future dates or amounts and
    compare the scenario to the baseline.
-   Acceptance: scenario changes are isolated from actual records; both
    baseline and scenario use the same forecast engine; UI shows balance
    difference and shortage changes.

## 7. Functional Requirements

1.  Dashboard with KPI cards, transaction list, upcoming
    bills/collections, forecast chart, and alert panel.
2.  Customer CRUD and customer-specific transaction history.
3.  Credit-sale and repayment entry; partial repayments supported.
4.  Supplier CRUD, bill creation, partial/full payment records.
5.  Expense entry with category, date, amount, and payment source.
6.  Forecast generation for 14 calendar days.
7.  Configurable cash safety buffer.
8.  Alerts for negative projected balance and safety-buffer breach.
9.  Scenario creation with editable hypothetical events and comparison.
10. Search, filter, form validation, loading, empty, and error states.
11. Demo seed data and a resettable demo environment.
12. Audit metadata for create/update/reversal operations where
    implemented.

## 8. Financial Rules

-   Actual available cash is a recorded balance, not the sum of cash
    plus receivables.
-   Credit sales increase receivables; they do not increase cash until
    repayment is recorded.
-   A supplier bill increases payables; it does not decrease cash until
    a payment is recorded.
-   Forecasted inflows are estimates with dates and confidence/status
    labels.
-   Moving a planned payment date does not erase the liability.
-   Scenario events must not mutate the actual ledger.
-   Use a consistent money representation. Preferred: integer paise in
    storage/API; display INR with Indian grouping.
-   Date-only due dates use the merchant's configured business timezone;
    default `Asia/Kolkata`.

## 9. Success Metrics for Demo

-   A new user can understand cash, receivables, and payables within 30
    seconds.
-   A repayment updates the customer balance and cash position
    correctly.
-   A supplier payment updates payable and cash correctly.
-   Forecast and shortage alert recalculate after relevant changes.
-   A What-If scenario demonstrates a visible baseline-versus-scenario
    difference.
-   No critical flow depends on Gemini or external payment integrations.

## 10. Risks and Mitigations

-   **Forecast trust:** show assumptions and item-level contributors.
-   **Bad input data:** validate dates, amounts, and transaction
    relationships.
-   **Over-scoping:** defer AI, advanced notifications, and CSV tooling
    until core flows work.
-   **Misleading financial interpretation:** label forecasts as
    estimates and never describe them as guarantees.
-   **Security:** enforce merchant ownership on every server-side
    read/write.

## 11. Phase Plan

-   Phase 1: core ledger, supplier bills/expenses, forecast, alerts,
    What-If.
-   Phase 2: repayment schedules, budget alerts, reports, basic
    reminders.
-   Phase 3: Gemini explanations, summaries, CSV import/export, advanced
    notifications.
-   Phase 4: production hardening, expanded roles, backup/restore,
    observability, and approved integrations.
