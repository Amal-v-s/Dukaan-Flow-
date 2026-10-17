# DukaanFlow --- Architecture

## 1. High-Level Architecture

``` mermaid
flowchart TD
    U[Merchant in Browser] --> FE[React + TypeScript Frontend]
    FE --> API[FastAPI /api/v1]
    API --> AUTH[Authentication and Membership Checks]
    API --> SVC[Domain Services]
    SVC --> LEDGER[Ledger and Payment Services]
    SVC --> FORECAST[Deterministic Forecast Engine]
    SVC --> SCENARIO[What-If Scenario Engine]
    LEDGER --> REPO[Firestore Repository Layer]
    FORECAST --> REPO
    SCENARIO --> FORECAST
    REPO --> DB[(Google Cloud Firestore)]
    API -. Phase 3 only .-> AI[Gemini / Vertex AI Explanation Layer]
    API --> OBS[Structured Logs and Health Metrics]
```

## 2. Layers

### Frontend

Responsible for navigation, forms, charts, state presentation, and user
feedback. It must not be the authority for balances or authorization.

### API Layer

FastAPI routers validate requests, derive authenticated identity,
enforce access rules, call services, and return typed response models.

### Domain Services

-   Customer ledger service.
-   Supplier bill/payment service.
-   Expense and cash movement service.
-   Dashboard aggregation service.
-   Forecast service.
-   Scenario service.
-   Audit service.

### Repository Layer

Owns Firestore reads/writes and query composition. Every repository
operation receives an authorized business context.

### Forecast Engine

Pure deterministic functions. Given the same normalized input events, it
returns the same output. No network calls or LLM dependency.

### AI Explanation Layer (Phase 3)

Receives precomputed facts and returns explanatory prose. It cannot
mutate records or determine financial totals.

## 3. Data Flow for a Repayment

1.  Request arrives with authenticated user.
2.  Membership and customer ownership are checked.
3.  Service computes current outstanding balance from valid ledger
    entries.
4.  Amount/date/method are validated.
5.  Ledger entry and cash movement are written consistently.
6.  Audit event is recorded.
7.  Dashboard and forecast are recalculated from canonical data.
8.  API returns the updated customer balance and movement summary.

## 4. Data Flow for Forecast

1.  Resolve current available cash from canonical posted movements.
2.  Collect future eligible inflows and outflows.
3.  Exclude events already reflected in current cash.
4.  Normalize events by business date.
5.  Calculate daily balances over 14 days.
6.  Detect zero and safety-buffer breaches.
7.  Attach source references for contributors.
8.  Return forecast and assumptions.

## 5. Deployment Topology

-   React frontend hosted separately or served by a static host.
-   FastAPI container deployed to Cloud Run.
-   Firestore for application data.
-   Cloud Logging/Monitoring for diagnostics.
-   Secret Manager for secrets.
-   Vertex AI integration only when Phase 3 is approved.

## 6. Architecture Constraints

-   No direct privileged Firestore access from the browser.
-   No financial arithmetic delegated to AI.
-   Scenario computations never write to real ledger collections.
-   All tenant-owned data access is authorized server-side.
-   Do not claim live bank/UPI integration without a separately
    implemented and authorized provider integration.
