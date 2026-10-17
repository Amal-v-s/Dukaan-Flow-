# DukaanFlow --- Delivery Roadmap

## Phase 1 --- Core MVP

**Objective:** Demonstrate the complete ledger-to-forecast-to-simulation
loop.

Deliverables: 1. Desktop-first app shell and seeded dashboard. 2.
Customer ledger with credit sales and partial repayments. 3. Supplier
records, bills, payments, and expenses. 4. Deterministic 14-day
cash-flow engine. 5. Shortage alerts with dates, thresholds, and
contributors. 6. What-If Simulator with baseline/scenario comparison. 7.
Core tests and demo reset process.

Exit criteria: - All six features work together. - Ledger changes update
relevant balances and forecast. - Simulations never mutate actual
records. - Financial calculations have unit tests. - A clean end-to-end
demo can be completed reliably.

## Phase 2 --- Business Management

Deliverables: - Repayment schedules and instalments. - Missed-payment
tracking. - Budget configuration and threshold alerts. - Basic
income/expense/receivables/payables reports. - Basic in-app reminders.

Exit criteria: - Schedules reconcile with customer balances. - Budgets
use actual recorded expenses. - Reports reconcile with canonical
records.

## Phase 3 --- AI and Automation

Deliverables: - Gemini-powered explanations grounded in
server-calculated facts. - Business summaries. - Data-backed
suggestions. - CSV import/export with validation and safe error
handling. - Advanced notifications through supported providers.

Exit criteria: - AI unavailable state falls back gracefully. - AI does
not invent or alter financial facts. - Imported data is validated and
previewed before commit. - Notifications require appropriate
permissions/approval.

## Phase 4 --- Production Readiness

Deliverables: - Strong authentication and role-based authorization. -
Business-level data isolation tests. - Backup and restore. -
Observability, alerting, and incident response notes. - Accessibility
and responsive polish. - Performance testing and deployment rollback. -
Privacy, terms, and compliance review before real merchant use.

## Prioritization Rule

Do not begin Phase 2 until Phase 1 exit criteria are met. Do not add AI
to compensate for missing deterministic logic. Prefer a smaller complete
product over many unfinished screens.
