# DukaanFlow --- Phase 1 Implementation Plan

## Objective

Deliver a working, demo-ready end-to-end product connecting the merchant
ledger to a deterministic 14-day forecast and an isolated What-If
Simulator.

## Phase 1 Scope

1.  Dashboard with sample business data.
2.  Customer udhaar ledger and partial repayments.
3.  Supplier bills and expense tracking.
4.  Deterministic 14-day cash-flow forecast.
5.  Cash-shortage alerts with clear explanations.
6.  What-If Simulator with before/after comparison.

## Recommended Implementation Subphases

### Phase 1A --- Foundation and Shell

-   Set up repository, frontend, backend, and environment configuration.
-   Establish design tokens and responsive desktop shell.
-   Add navigation for Overview, Khata, Suppliers, Transactions, Cash
    Flow, Simulator.
-   Add deterministic demo seed data.
-   Define API schemas, money/date utilities, and error format.
    **Exit:** app runs locally, routes load, seed data is repeatable.

### Phase 1B --- Customer Khata

-   Customer list and detail views.
-   Create customer and credit-sale forms.
-   Partial/full repayment form.
-   Calculate outstanding balance on backend.
-   Update dashboard receivables and actual cash after repayment.
    **Exit:** customer balance reconciles after a repayment and tests
    pass.

### Phase 1C --- Supplier Bills and Expenses

-   Supplier list and detail.
-   Create supplier bill and record partial/full payments.
-   Add expense entry and category.
-   Separate unpaid obligations from posted cash outflows. **Exit:**
    bill outstanding, paid status, and cash movements reconcile.

### Phase 1D --- Forecast Engine

-   Normalize future inflow/outflow events.
-   Calculate daily closing balances over 14 days.
-   Include expected collection dates as estimates.
-   Avoid double-counting movements already included in opening cash.
-   Return contributor references and assumptions. **Exit:**
    deterministic unit tests cover expected cases and edge cases.

### Phase 1E --- Shortage Alerts

-   Configure safety buffer.
-   Detect projected balances below zero and below buffer.
-   Explain date, threshold, and contributing bills/collections.
-   Link alert details to source records. **Exit:** alert changes
    correctly when underlying data changes.

### Phase 1F --- What-If Simulator

-   Choose an eligible future event or add a hypothetical event.
-   Change event date/amount or add a planned expense.
-   Calculate baseline and scenario with the same engine.
-   Show balance delta, minimum balance/date, and shortage status.
-   Reset scenario without changing real records. **Exit:** scenario
    improves/worsens forecast correctly and actual records remain
    unchanged.

### Phase 1G --- Demo Hardening

-   Empty/loading/error states.
-   Form validation and duplicate-submit prevention.
-   Responsive pass.
-   Seed/reset instructions.
-   End-to-end demo run and bug fixes.
-   Verify no critical flow depends on AI or external payment APIs.
    **Exit:** a reliable demo can be completed from start to finish.

## Suggested Build Order

1.  Foundation and shell.
2.  Customer Khata.
3.  Supplier bills and expenses.
4.  Forecast engine.
5.  Shortage alerts.
6.  What-If Simulator.
7.  End-to-end test and polish.

## Phase 1 Definition of Done

-   [ ] Dashboard shows available cash, receivables, payables, upcoming
    obligations, and forecast summary.
-   [ ] Credit sale increases receivables but not available cash.
-   [ ] Partial repayment decreases receivables and increases actual
    cash.
-   [ ] Unpaid supplier bill increases payables but does not decrease
    cash.
-   [ ] Supplier payment decreases payable and actual cash.
-   [ ] Paid expense decreases actual cash exactly once.
-   [ ] Forecast covers 14 days and is deterministic.
-   [ ] Shortage alert explains its contributing events.
-   [ ] What-If comparison shows baseline and hypothetical values.
-   [ ] Scenario never mutates actual ledger records.
-   [ ] Critical calculations have automated tests.
-   [ ] Demo data is clearly marked as illustrative.
