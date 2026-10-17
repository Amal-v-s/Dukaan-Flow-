# DukaanFlow --- Production Coding Rules

## 1. General

-   Ship readable, typed, testable code rather than clever abstractions.
-   No feature is complete until loading, empty, error, validation, and
    success states exist.
-   Avoid TODO placeholders in critical financial paths.
-   Do not claim integrations that are not implemented.
-   Keep the MVP dependency footprint small.

## 2. Frontend

-   TypeScript strict mode enabled.
-   Avoid `any`; use `unknown` and narrow it when needed.
-   Keep feature components organized by domain.
-   Use a shared API client with typed request/response models.
-   Do not calculate authoritative balances in components.
-   Use shared INR/date formatters.
-   Keep forms controlled or use a documented form library.
-   Add accessible labels, keyboard behavior, and visible focus styles.
-   Do not place secrets in client bundles or `VITE_*` variables.
-   Sanitize/render user-provided text as text, not raw HTML.
-   Avoid unbounded global state; use local state for local
    interactions.

## 3. Backend

-   Python type hints required for public service functions.
-   Pydantic models validate external input and response shapes.
-   Keep route handlers thin.
-   Business logic belongs in services/domain functions.
-   Repository code owns Firestore query/write details.
-   Use centralized exception mapping and structured logs.
-   Never expose raw exceptions to users.
-   Avoid blocking I/O inside async handlers unless safely offloaded.
-   Apply pagination and query limits.
-   Use transaction/batch semantics for coupled money records.

## 4. Financial Logic

-   Integer paise only for persisted/calculated monetary amounts.
-   No `float` for currency arithmetic.
-   A single canonical source of truth per movement.
-   No double-counting between ledger records and cash events.
-   Scenario data is isolated from actual ledger collections.
-   Every forecast contributor references a source record or explicit
    hypothetical event.
-   All calculations must have tests for normal, boundary, and invalid
    cases.
-   Reversals must preserve the original record and audit trail.

## 5. Git and Code Review

-   Use feature branches for substantial work.
-   Keep commits focused and descriptive.
-   Never commit `.env`, secrets, credentials, user exports, or
    production data.
-   Review schema/API changes alongside docs and tests.
-   Require lint, type checks, tests, and build before merge.
-   Do not merge known authorization or financial-integrity regressions.

## 6. Observability

-   Use structured logs with request IDs.
-   Do not log secrets, authentication tokens, UPI credentials, or
    unnecessary personal data.
-   Track API errors, latency, and forecast failures.
-   Add actionable error messages without exposing implementation
    details.
