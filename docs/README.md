# DukaanFlow Documentation Pack

This folder contains the canonical product, technical, architecture, security, design, API, testing, and delivery documents for **DukaanFlow** (*Track Every Rupee. Plan Every Move.*).

---

## 1. Document Index

| Document | Purpose / Scope |
| :--- | :--- |
| [`01_PRD.md`](file:///d:/gch/Dukaan-Flow-/docs/01_PRD.md) | **Product Requirements Document:** Target audience (kirana merchants), problem statements, core features, and acceptance criteria. |
| [`02_TRD.md`](file:///d:/gch/Dukaan-Flow-/docs/02_TRD.md) | **Technical Requirements Document:** Architecture, tech stack (React + TypeScript Strict Mode, FastAPI, Google Cloud Run, Firestore). |
| [`03_DATABASE_SCHEMA.md`](file:///d:/gch/Dukaan-Flow-/docs/03_DATABASE_SCHEMA.md) | **Database Schema:** Document-scoped Firestore collections (`businesses/{businessId}/...`), entity models, and indexing strategies. |
| [`04_AUTH_SECURITY.md`](file:///d:/gch/Dukaan-Flow-/docs/04_AUTH_SECURITY.md) | **Authentication & Security:** Firebase Auth, JWT bearer verification, tenant isolation, CORS policies, and secret management. |
| [`05_API_SPEC.md`](file:///d:/gch/Dukaan-Flow-/docs/05_API_SPEC.md) | **REST API Specifications:** Detailed request/response contracts for `/api/v1` (Khata, Suppliers, Expenses, Forecast, Scenarios, Management). |
| [`06_ENGINEERING_RULES.md`](file:///d:/gch/Dukaan-Flow-/docs/06_ENGINEERING_RULES.md) | **Engineering Conventions:** Coding standards, integer paise currency rule, folder structures, Git workflow, and naming conventions. |
| [`07_AI_ASSISTANT.md`](file:///d:/gch/Dukaan-Flow-/docs/07_AI_ASSISTANT.md) | **AI Assistant Grounding Contract:** Strict rules for Gemini Vertex AI integration (explaining deterministic facts only, zero financial arithmetic). |
| [`09_TESTING_DEPLOYMENT.md`](file:///d:/gch/Dukaan-Flow-/docs/09_TESTING_DEPLOYMENT.md) | **Testing & Deployment Strategy:** Automated unit/integration testing with `pytest`, TypeScript builds, Docker, and Cloud Run deployment. |
| [`APP_FLOW.md`](file:///d:/gch/Dukaan-Flow-/docs/APP_FLOW.md) | **Application Flow & UX Journeys:** Screen hierarchy, primary routes (`/`, `/customers`, `/suppliers`, `/transactions`, `/cash-flow`, `/simulator`, `/management`, `/settings`). |
| [`ARCHITECTURE.md`](file:///d:/gch/Dukaan-Flow-/docs/ARCHITECTURE.md) | **System Architecture:** Component topologies, data flow diagrams, deterministic forecast pipeline, and tenant boundary enforcement. |
| [`DELIVERY_ROADMAP.md`](file:///d:/gch/Dukaan-Flow-/docs/DELIVERY_ROADMAP.md) | **4-Phase Product Roadmap:** High-level milestones from Core Platform (Phase 1) to Production Scaling (Phase 4). |
| [`DESIGN.md`](file:///d:/gch/Dukaan-Flow-/docs/DESIGN.md) | **Design System ("Merchant Flow Precision"):** Shop-counter readable typography, color tokens (Emerald, Blue, Amber, Red), spacing, and component guidelines. |
| [`PRODUCTION_CODING_RULES.md`](file:///d:/gch/Dukaan-Flow-/docs/PRODUCTION_CODING_RULES.md) | **Production Coding Standards:** Immutability, error boundaries, input sanitization, and defensive programming guidelines. |
| [`PRODUCTION_SECURITY.md`](file:///d:/gch/Dukaan-Flow-/docs/PRODUCTION_SECURITY.md) | **Production Security Guardrails:** Zero secrets in source, least-privilege IAM roles, SQL/injection prevention, and tenant boundary isolation. |
| [`phase1_phases.md`](file:///d:/gch/Dukaan-Flow-/docs/phase1_phases.md) | **Phase 1 Implementation Plan (Core Platform):** Subphases 1A through 1G covering core khata, suppliers, deterministic forecast, alerts, and what-if simulator. *(Status: 100% Completed)* |
| [`phase2_phases.md`](file:///d:/gch/Dukaan-Flow-/docs/phase2_phases.md) | **Phase 2 Implementation Plan (Business Management):** Subphases 2A through 2H covering repayment plans, instalment tracking, expense budgets, summary reports, and in-app reminders. *(Status: 100% Completed)* |
| [`phase3_phases.md`](file:///d:/gch/Dukaan-Flow-/docs/phase3_phases.md) | **Phase 3 Implementation Plan (AI & Automation):** Subphases 3A through 3H covering grounded Gemini explanations, business summaries, CSV import/export, and notification controls. *(Status: Ready for Implementation)* |

---

## 2. Phased Delivery Status

* **Phase 1 (Core Platform):** 🏆 **100% Complete & Verified**
  - Canonical Customer Khata and Supplier Payables.
  - Pure deterministic 14-day cash-flow forecast engine with shortage detection.
  - Isolated What-If Simulator with verified zero database mutation.
  - 32/32 automated tests passing.
* **Phase 2 (Business Management):** 🏆 **100% Complete & Verified**
  - Customer Repayment Plans (full payment & multi-part instalment schedules).
  - Derived overdue tracking (`days_overdue`), plan cancellation with audit events.
  - Expense Category Budgets with 75%, 90%, and 100% threshold breach alerts.
  - Date-filtered Financial Reports (summary, expenses, receivables, payables).
  - Deduplicated In-App Reminders (rolling 7-day lookahead, acknowledgment).
  - 45/45 automated tests passing; production build verified; live UI browser tested.
* **Phase 3 (AI & Automation):** ⏳ **Ready for Implementation**
  - Grounded Gemini Vertex AI summaries for alerts and forecast insights.
  - Merchant-approved reminder drafting (no autonomous sending).
  - Structured CSV import (with preview and validation) and export.
  - Multi-tenant Firestore persistence & Cloud Run packaging.

---

## 3. Non-Negotiable Architectural Invariants

Every agent and developer working on DukaanFlow must uphold these rules without exception:

1. **Integer Paise Everywhere:**
   - All currency values in schemas, domain logic, APIs, and calculations MUST be integer paise (`amount_paise`).
   - Float is strictly prohibited for monetary arithmetic. Format to INR (`₹1,48,200`) strictly at presentation boundaries.
2. **Strict Cash vs. Ledger Separation:**
   - **Cash in Hand** is an explicit, verified asset balance.
   - **Credit Sales** increase receivables; they **do not** inflate cash until repaid.
   - **Supplier Bills** increase payables; they **do not** reduce cash until paid.
   - **Expenses** reduce cash immediately upon recording.
3. **Deterministic Forecast Engine:**
   - 14-day cash-flow projections and deficit calculations are computed **exclusively** in deterministic Python functions.
   - Zero LLM or AI arithmetic for balances, projections, or shortage detection.
4. **Isolated What-If Simulator:**
   - Scenario simulations run in ephemeral, isolated sandboxes and **must never mutate** the active ledger or business state.
5. **Tenant Isolation:**
   - Every read and write must be strictly partitioned by `businesses/{businessId}/`.
   - Never trust client-supplied business identity without server-side validation.
6. **No Autonomous External Actions:**
   - Reminders are strictly in-app unless explicit external SMS/WhatsApp integrations and merchant approval are configured.
   - DukaanFlow does not lend money, originate loans, execute automatic bank debits, or charge arbitrary late fees.

---

> For real-time project state, active branch notes, and session logs, consult [`memory.md`](file:///d:/gch/Dukaan-Flow-/memory.md).
