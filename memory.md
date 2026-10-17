# DukaanFlow --- Team & Agent Shared Memory

> **Notice to all Agents & Collaborators:**
> This is a living document tracking the project state, architectural invariants, and phased progress.
> - **Before starting work:** Review this file and the corresponding specs in [`docs/`](file:///d:/gch/Dukaan-Flow-/docs).
> - **After completing any subphase/task:** Update the status, logs, modified files, and verified evidence in this file.

---

## 1. Project Overview

* **Product:** DukaanFlow
* **Tagline:** Track Every Rupee. Plan Every Move.
* **Team:** C Minus (Google Cloud Hackathon)
* **Target Audience:** Indian small merchants, kirana stores, and local wholesalers.
* **Primary Currency:** INR (₹)
* **Core Tech Stack:**
  * **Frontend:** React + TypeScript (Strict Mode), Vite, React Router, Tailwind CSS / Token System, Lucide Icons.
  * **Backend:** Python 3.11+ + FastAPI (`/api/v1`), Pydantic models.
  * **Database:** Google Cloud Firestore (document-scoped under `businesses/{businessId}/`).
  * **Deployment Target:** Google Cloud Run (Backend) + Static Hosting (Frontend).
  * **AI Layer (Phase 3 only):** Gemini via Vertex AI strictly for narrative summaries of server-calculated facts.

---

## 2. Non-Negotiable Architectural Invariants

Every agent and developer working on this codebase must adhere strictly to these rules:

1. **Integer Paise Everywhere:**
   * All monetary values in database, models, APIs, and business logic MUST be stored and computed as integer paise (`amount_paise`).
   * **Never** use binary floating-point (`float`) for currency math.
   * Format into decimal INR (`₹1,48,200`) only at frontend presentation boundaries using tabular numerals (`font-variant-numeric: tabular-nums`).

2. **Strict Cash vs. Ledger Separation:**
   * **Actual Available Cash** is an explicit, recorded balance.
   * **Credit Sales** increase receivables; they **do not** increase cash until repayment is recorded.
   * **Supplier Bills** increase payables; they **do not** decrease cash until a payment is recorded.
   * **Paid Expenses** decrease cash immediately (no double-counting with cash events).

3. **Deterministic Forecast Engine:**
   * 14-day cash-flow forecasting is calculated exclusively in deterministic, unit-tested Python functions.
   * **No LLM or AI arithmetic** for balances, projections, or shortage detection.
   * Future cash projections must not double-count events already reflected in the opening cash balance.

4. **Isolated What-If Simulator:**
   * Hypothetical events, date changes, and amount overrides must remain strictly isolated.
   * The simulator **must never mutate the actual ledger or live business records**.

5. **Tenant Isolation & Security:**
   * Every query and mutation must enforce `businesses/{businessId}/` scope server-side.
   * Never trust client-supplied `business_id` or `user_id` without verifying identity claims.
   * No service account JSONs, secrets, or API keys in source control or frontend bundles.

6. **Design System ("Merchant Flow Precision"):**
   * Follow the tokens and layout defined in [`docs/DESIGN.md`](file:///d:/gch/Dukaan-Flow-/docs/DESIGN.md).
   * Primary: Growth Emerald (`#16A36A`), Projection Blue (`#6D8FE8`), Warning Amber (`#E9A23B`), Alert Red (`#DC5555`).
   * Anti-glare, shop-counter friendly surfaces (Canvas `#F7F8FA`, Card `#FFFFFF`).

---

## 3. Phase 1 Implementation Tracker

| Subphase | Name | Scope / Focus | Status | Owner / Agent |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1A** | Foundation & Shell | Repo setup, Vite + FastAPI, design tokens, responsive shell, routing, seed data | ✅ **COMPLETED** | Antigravity (Gravitas) |
| **Phase 1B** | Customer Khata | Customer CRUD, credit sales, partial repayments, balance calculation | ✅ **COMPLETED** | Antigravity (Gravitas) |
| **Phase 1C** | Suppliers & Expenses | Supplier bills, partial payments, categorized expenses, cash outflow sync | ✅ **COMPLETED** | Antigravity (Gravitas) |
| **Phase 1D** | Forecast Engine | Pure deterministic 14-day closing balance engine, contributor tracing | ✅ **COMPLETED** | Antigravity (Gravitas) |
| **Phase 1E** | Shortage Alerts | Safety buffer breach detection, alert detail linking to source events | ✅ **COMPLETED** | Antigravity (Gravitas) |
| **Phase 1F** | What-If Simulator | Hypothetical event overrides, baseline vs scenario comparison, zero ledger mutation | ✅ **COMPLETED** | Antigravity (Gravitas) |
| **Phase 1G** | Demo Hardening | Form validation, empty/loading/error states, seed reset script, E2E demo run | ✅ **COMPLETED** | Antigravity (Gravitas) |
| **All Phase 1**| **Full Definition of Done** | **End-to-End Ledger, Deterministic Forecast, Alerts, and What-If Simulator** | 🏆 **100% COMPLETE** | Antigravity (Gravitas) |
| **Phase 2A-2G** | Business Management Features | Repayment plans, instalments, overdue tracking, budgets, reports, in-app reminders, dashboard/forecast integration | ✅ **COMPLETED** | Codex |
| **Phase 2H** | Release Hardening | Acceptance tests, accessibility/responsive review, full E2E, regression verification | ✅ **COMPLETED** | Antigravity (Gravitas) |
| **All Phase 2** | **Full Definition of Done** | **Repayment Plans, Budgets, Reports, In-App Reminders, Acceptance Tests** | 🏆 **100% COMPLETE** | Antigravity (Gravitas) |

---

## 4. Detailed Subphase Status & Log

### Current Status: All Phase 1 Subphases Completed (1A - 1G)
* **Milestone:** Phase 1 Definition of Done (DoD) fully satisfied and verified. Ready for demo or Phase 2.
* **Key Achievements:**
  - 100% Integer paise arithmetic (`amount_paise`) throughout domain models, APIs, and UI formatters.
  - Strict separation of Cash in Hand vs Customer/Supplier Ledger Obligations.
  - Pure deterministic 14-day cash-flow forecast in Python (zero LLM/AI math).
  - Dynamic cash shortage and safety buffer breach alerts with root-cause attribution chips.
  - Isolated What-If Simulator with verified ZERO database mutation.
  - Automated verification suite: **32/32 tests passing** in under 1 second; clean TypeScript build.
* **Next Active Phase:** Phase 2H release hardening and acceptance coverage.

---

### [Phase 1A] Foundation and Shell
* **Status:** ✅ **COMPLETED** (Verified 2026-10-17)

---

### [Phase 1B] Customer Khata
* **Status:** ✅ **COMPLETED** (Verified 2026-10-17)
* **Deliverables:**
  - [x] Customer creation API (`POST /api/v1/customers`).
  - [x] Customer detail & ledger history endpoints (`GET /api/v1/customers/{id}`, `GET /api/v1/customers/{id}/ledger`).
  - [x] Ledger entry creation API (`POST /api/v1/customers/{id}/ledger-entries`) for credit sales and repayments.
  - [x] Calculation of outstanding balance = posted credit sales - posted repayments.
  - [x] Reject overpayment with HTTP 400 and clear error message.
  - [x] Auto-synchronization of valid repayment into cash book (cash inflow) and dashboard available cash.
  - [x] Interactive Customer Khata UI with customer detail drawer, +Credit modal, and Repay modal.
* **Files Created / Modified:**
  - `backend/app/domain/ledger.py` (Pure balance calculation and repayment validator)
  - `backend/app/schemas/customer.py` (Typed Pydantic request/response schemas)
  - `backend/app/services/customer_service.py` (Customer ledger service, balance reconciliation, cashbook sync)
  - `backend/app/api/v1/customers.py` (FastAPI router for CRUD, ledger, entries)
  - `backend/app/api/v1/dashboard.py` (Upcoming item filter fix for credit sales)
  - `backend/tests/test_ledger.py` (Unit & API integration tests for customer ledger)
  - `frontend/src/features/customers/CustomersPage.tsx` (Interactive customer khata table, drawer, add customer modal, credit modal, repayment modal)
* **Verification & Evidence:**
  - `python -m pytest backend`: **17 passed in 0.67s** (covers domain balance arithmetic, repayment limits, overpayment rejection, and cashbook sync).
  - `npm run build`: **Built in 537ms** with 0 errors.

---

### [Phase 1C] Supplier Bills and Expenses
* **Status:** ✅ **COMPLETED** (Verified 2026-10-17)
* **Deliverables:**
  - [x] Supplier management and bill creation (`POST /api/v1/suppliers`, `POST /api/v1/supplier-bills`).
  - [x] Bill partial/full payments with status tracking (`unpaid`, `partially_paid`, `paid`).
  - [x] Payment overpayment rejection (cannot pay more than bill remaining amount, HTTP 400).
  - [x] Categorized expense recording (`POST /api/v1/expenses`).
  - [x] Sync paid expenses and supplier payments with actual cash movements (reduces available cash).
  - [x] Interactive UI on `SuppliersPage` (Bill creation modal, Pay bill modal, status filter) and `TransactionsPage` (Record expense modal, category filter).
* **Files Created / Modified:**
  - `backend/app/schemas/supplier.py` (Typed schemas for suppliers, bills, payments, expenses)
  - `backend/app/services/supplier_service.py` (Service managing bills, payments, overpayment rejection, expenses, cash outflow sync)
  - `backend/app/api/v1/suppliers.py` (FastAPI router for suppliers, bills, payments)
  - `backend/app/api/v1/expenses.py` (FastAPI router for expenses)
  - `backend/app/main.py` (Registered expenses router)
  - `backend/tests/test_suppliers_expenses.py` (Unit & API tests for bills, payments, overpayments, expenses, and cashbook sync)
  - `frontend/src/features/suppliers/SuppliersPage.tsx` (Interactive suppliers table, add bill modal, pay bill modal, status filters)
  - `frontend/src/features/transactions/TransactionsPage.tsx` (Interactive cashbook table, add expense modal, direction & category filters)
* **Verification & Evidence:**
  - `python -m pytest backend`: **20 passed in 0.58s** (covers bill creation, unpaid non-movement, partial payment, overpayment rejection, and expense cash sync).
  - `npm run build`: **Built in 456ms** with TypeScript strict mode, 0 errors.

---

### [Phase 1D] Forecast Engine
* **Status:** ✅ **COMPLETED** (Verified 2026-10-17)
* **Deliverables:**
  - [x] Pure deterministic 14-day projection engine in backend domain layer (`backend/app/domain/forecast.py`).
  - [x] Correct daily closing balance calculation with eligible future movements (`closing[d] = opening[d] + inflows[d] - outflows[d]`).
  - [x] Prevention of double-counting movements reflected in opening cash balance.
  - [x] Unit test suite verifying boundary dates, leap days, and edge cases (`backend/tests/test_forecast.py`).
  - [x] API endpoint updated and verified (`backend/app/api/v1/cashflow.py`, `backend/tests/test_api.py`).
* **Files Created / Modified:**
  - `backend/app/domain/forecast.py` (Pure deterministic forecast engine with data classes and edge-case validation)
  - `backend/app/api/v1/cashflow.py` (FastAPI forecast router wired to domain engine)
  - `backend/tests/test_forecast.py` (Unit tests for formula, leap years, boundary months, multi-events, negative balances, and type safety)
  - `backend/tests/test_api.py` (API integration tests for forecast endpoint)
* **Verification & Evidence:**
  - `python -m pytest backend`: **26 passed in 0.52s** (covers domain forecast, leap year, same-day movements, double-counting protection, and API contract).
  - `npm run build`: **Built in 446ms** with TypeScript strict mode, 0 errors.

---

### [Phase 1E] Shortage Alerts
* **Status:** ✅ **COMPLETED** (Verified 2026-10-17)
* **Deliverables:**
  - [x] Configurable merchant cash safety buffer floor.
  - [x] Detection of projected balances below zero (critical deficit) and below safety buffer (warning).
  - [x] Contributing source event attribution (links directly to Coastal Wholesale bill and Ravi Stores collections).
  - [x] Dynamic alert generation and acknowledgement API (`GET /api/v1/alerts`, `PATCH /api/v1/alerts/{id}`).
  - [x] Interactive Alert Banner in `DashboardPage.tsx` with one-click dismiss, attribution chips, and simulator link.
  - [x] Alert Panel and expandable day breakdown in `CashFlowPage.tsx`.
* **Files Created / Modified:**
  - `backend/app/schemas/alert.py` (Typed Pydantic alert schemas)
  - `backend/app/services/alert_service.py` (Deterministic alert derivation from forecast and threshold)
  - `backend/app/api/v1/alerts.py` (FastAPI router for alerts and acknowledgements)
  - `backend/app/main.py` (Registered alerts router)
  - `backend/tests/test_alerts.py` (Unit and API tests for alerts and acknowledgement lifecycle)
  - `frontend/src/features/dashboard/DashboardPage.tsx` (Dynamic alert banner with attribution and dismiss action)
  - `frontend/src/features/cashflow/CashFlowPage.tsx` (Alerts card with record links and expandable daily breakdown)
* **Verification & Evidence:**
  - `python -m pytest backend`: **28 passed in 0.56s** (covers alert derivation, deficit math, acknowledgement lifecycle, and forecast contracts).
  - `npm run build`: **Built in 455ms** with TypeScript strict mode, 0 errors.

---

### [Phase 1F] What-If Simulator
* **Status:** ✅ **COMPLETED** (Verified 2026-10-17)
* **Deliverables:**
  - [x] Scenario models and service supporting scenario creation, event shifting (date/amount overrides), and ad-hoc hypothetical expenses/inflows (`backend/app/services/scenario_service.py`).
  - [x] Run both baseline and scenario through the exact same pure deterministic forecast engine (`backend/app/domain/forecast.py`).
  - [x] Calculate day-by-day balance delta, minimum balance/date, and shortage status resolution.
  - [x] Strict isolation invariant: verify that simulating scenarios causes ZERO mutations to actual customer, supplier, transaction, or business records (`test_strict_isolation_invariant`).
  - [x] Full REST API endpoints: `POST /api/v1/scenarios`, `GET /api/v1/scenarios`, `POST /api/v1/scenarios/{id}/events`, `POST /api/v1/scenarios/{id}/forecast`.
  - [x] Interactive UI in `frontend/src/features/simulator/SimulatorPage.tsx` with dynamic baseline vs scenario trajectory comparison bars, event shift toggles, and day-by-day delta table.
* **Files Created / Modified:**
  - `backend/app/schemas/scenario.py` (Typed Pydantic request/response schemas for scenarios, events, and comparison)
  - `backend/app/services/scenario_service.py` (Isolated scenario execution engine with snapshot invariant verification)
  - `backend/app/api/v1/scenarios.py` (FastAPI router for scenario CRUD, event additions, and forecast comparison)
  - `backend/app/main.py` (Registered scenarios router)
  - `backend/tests/test_scenarios.py` (Comprehensive unit & integration tests covering scenario resolution and zero-mutation invariant)
  - `frontend/src/features/simulator/SimulatorPage.tsx` (Dynamic simulation dashboard connected to backend API)
* **Verification & Evidence:**
  - `python -m pytest backend`: **31 passed in 0.68s** (covers scenario forecasting, deficit resolution, and zero database mutation invariant).
  - `npm run build`: **Built in 581ms** with TypeScript strict mode, 0 errors.

---

### [Phase 1G] Demo Hardening & Verification
* **Status:** ✅ **COMPLETED** (Verified 2026-10-17)
* **Deliverables:**
  - [x] Empty states, loading skeletons, and accessible form validations across all forms (`CustomersPage`, `SuppliersPage`, `TransactionsPage`, `DashboardPage`, `CashFlowPage`, `SimulatorPage`).
  - [x] Duplicate submission prevention on all money forms (`disabled={submitting}` and asynchronous lock guards).
  - [x] Seed data reset flow tested and verified via UI button in header and `POST /api/v1/seed/reset`.
  - [x] Complete E2E walkthrough script executed and verified (`backend/tests/test_e2e_walkthrough.py`).
  - [x] Verified zero dependency on external AI arithmetic or third-party payment gateways for critical Phase 1 flows.
* **Files Created / Modified:**
  - `frontend/src/components/layout/Header.tsx` (Integrated Reset Demo button with live reload & status feedback)
  - `backend/tests/test_e2e_walkthrough.py` (Full end-to-end integration test validating the entire Phase 1 Definition of Done)
* **Verification & Evidence:**
  - `python -m pytest backend`: **32 passed in 1.86s** (100% green across all unit, domain, API, and E2E walkthrough suites).
  - `npm run build`: **Built in 521ms** with TypeScript strict mode, 0 errors, 0 lint warnings.


---

## Phase 2 Implementation Status

### Current Status: Phase 2 Definition of Done 100% Complete & Verified (2A - 2H)
* **Milestone:** Full Business Management Suite (Repayment Plans, Budgets, Reports, In-App Reminders, Forecast/Dashboard Integration, and Automated Acceptance Testing).
* **Phase 2A/2B (Repayment Plans & Instalments):** Full-payment & multi-part instalment schedules. Enforces exact balance allocation, ascending date ordering, integer paise validation, single ledger entry + cashbook inflow per payment, and idempotency keying by `payment_id`.
* **Phase 2C (Overdue Tracking & Cancellation):** Read-derived overdue status from ISO dates; cancellation with mandatory reason restricted to unpaid plans only.
* **Phase 2D (Expense Budgets & Thresholds):** Real-time budget tracking on paid expenses with 75%, 90%, and 100% threshold breach alerts; strict isolation preventing supplier bills from polluting expenses.
* **Phase 2E (Financial Reports):** Clean date-filtered summaries separating cash inflows/outflows from receivables, payables, active plans, and budgets.
* **Phase 2F (In-App Reminders):** Rolling 7-day lookahead for customer instalments and supplier bills, deduplicated and acknowledgeable.
* **Phase 2G (Forecast & Dashboard Integration):** Dashboard counters for upcoming instalments, overdue plans, and budget alerts; forecast engine replaces allocated credit sales with scheduled instalments without double-counting; FIFO debt allocation for counter khata repayments.
* **Phase 2H (Release Hardening & Verification):**
  - Added comprehensive test suites:
    - `backend/tests/test_repayment_plans.py`: 4 tests covering schedules, date ordering, partial payments, idempotency, overpayment rejection, and cancellation.
    - `backend/tests/test_budgets_reports_reminders.py`: 3 tests covering category budgets, threshold triggers, supplier bill exclusion, date-filtered summary reports, and idempotent reminder acknowledgement.
    - `backend/tests/test_phase2_integration.py`: 2 tests covering dashboard alerts/instalments, forecast schedule integration without double-counting, and counter khata FIFO repayment allocation.
  - Verification & Evidence:
    - `python -m pytest backend`: **41 passed in 0.89s** (32 Phase 1 + 9 Phase 2 tests, 100% green).
    - `npm --prefix frontend run build`: **Built in 587ms** with TypeScript strict mode, 0 errors.
    - Live browser automation: End-to-end plan creation, budget creation, and reminders verified via browser subagent (`phase2_ui_verified_1792220850465.webp` and `management_page_completed_1792220951392.png`).
* **Next Active Phase:** Phase 3 (Persistent Firestore storage, Google Cloud Run deployment, and Gemini Vertex AI Grounded Summaries).

---

## 5. Phase Update Protocol (For All Agents & Contributors)

Whenever you finish working on a phase or significant milestone:
1. **Update the Status:** Change the subphase status in Section 3 and Section 4 to `IN PROGRESS` or `✅ COMPLETED`.
2. **Document Modified Files:** List all files created or edited under that subphase.
3. **Record Evidence:** Provide test run output, type check verification, or lint results.
4. **Log Decisions / Gotchas:** Add any architectural rationale or deviation from initial assumptions.
5. **Set Next Active Phase:** Clearly mark what the next agent or contributor should pick up.

---

## 6. Documentation Index

* [`docs/01_PRD.md`](file:///d:/gch/Dukaan-Flow-/docs/01_PRD.md) --- Product Requirements Document
* [`docs/02_TRD.md`](file:///d:/gch/Dukaan-Flow-/docs/02_TRD.md) --- Technical Requirements Document
* [`docs/03_DATABASE_SCHEMA.md`](file:///d:/gch/Dukaan-Flow-/docs/03_DATABASE_SCHEMA.md) --- Firestore Schema & Entity Specifications
* [`docs/04_AUTH_SECURITY.md`](file:///d:/gch/Dukaan-Flow-/docs/04_AUTH_SECURITY.md) --- Authentication & Application Security
* [`docs/05_API_SPEC.md`](file:///d:/gch/Dukaan-Flow-/docs/05_API_SPEC.md) --- REST API Specifications (`/api/v1`)
* [`docs/06_ENGINEERING_RULES.md`](file:///d:/gch/Dukaan-Flow-/docs/06_ENGINEERING_RULES.md) --- Engineering Conventions & Project Structure
* [`docs/07_AI_ASSISTANT.md`](file:///d:/gch/Dukaan-Flow-/docs/07_AI_ASSISTANT.md) --- AI Grounding Contract (Phase 3)
* [`docs/09_TESTING_DEPLOYMENT.md`](file:///d:/gch/Dukaan-Flow-/docs/09_TESTING_DEPLOYMENT.md) --- Testing Strategy & Cloud Run Deployment
* [`docs/APP_FLOW.md`](file:///d:/gch/Dukaan-Flow-/docs/APP_FLOW.md) --- Primary Navigation & User Journeys
* [`docs/ARCHITECTURE.md`](file:///d:/gch/Dukaan-Flow-/docs/ARCHITECTURE.md) --- System Architecture & Component Interaction
* [`docs/DELIVERY_ROADMAP.md`](file:///d:/gch/Dukaan-Flow-/docs/DELIVERY_ROADMAP.md) --- 4-Phase Roadmap & Milestones
* [`docs/DESIGN.md`](file:///d:/gch/Dukaan-Flow-/docs/DESIGN.md) --- Merchant Flow Precision Design System
* [`docs/PRODUCTION_CODING_RULES.md`](file:///d:/gch/Dukaan-Flow-/docs/PRODUCTION_CODING_RULES.md) --- Production Coding Guidelines
* [`docs/PRODUCTION_SECURITY.md`](file:///d:/gch/Dukaan-Flow-/docs/PRODUCTION_SECURITY.md) --- Security Rules & Boundary Safeguards
* [`docs/phase1_phases.md`](file:///d:/gch/Dukaan-Flow-/docs/phase1_phases.md) --- Detailed Phase 1 Subphases & DoD
* [`docs/phase2_phases.md`](file:///d:/gch/Dukaan-Flow-/docs/phase2_phases.md) --- Detailed Phase 2 Subphases & DoD
* [`docs/phase3_phases.md`](file:///d:/gch/Dukaan-Flow-/docs/phase3_phases.md) --- Detailed Phase 3 Subphases & DoD

