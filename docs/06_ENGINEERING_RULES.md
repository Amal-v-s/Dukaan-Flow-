# DukaanFlow --- Engineering Rules

## 1. Architecture Rules

-   Keep UI, API routes, business services, repositories, and domain
    calculations separate.
-   Frontend never contains privileged database credentials.
-   Financial calculations live in tested backend domain functions.
-   Forecast and scenario evaluation share the same calculation engine.
-   Do not call Gemini for arithmetic, ledger balances, or shortage
    detection.
-   Keep Phase 1 dependencies minimal.

## 2. Suggested Repository Layout

``` text
dukaanflow/
  frontend/
    src/
      app/
      components/
      features/
        dashboard/
        customers/
        suppliers/
        expenses/
        cashflow/
        simulator/
      lib/
      styles/
  backend/
    app/
      api/v1/
      core/
      schemas/
      services/
      repositories/
      domain/
        money.py
        ledger.py
        forecast.py
        scenarios.py
      main.py
    tests/
  infra/
    firestore.indexes.json
    cloudrun/
  docs/
```

## 3. Coding Conventions

-   Python: type hints, Pydantic schemas, clear service boundaries,
    Ruff/formatter, pytest.
-   TypeScript: strict mode, avoid `any`, ESLint, Prettier, typed API
    clients.
-   Use descriptive names and small functions.
-   Avoid duplicated calculations and duplicated status logic.
-   Avoid giant components and route handlers.
-   Keep comments focused on rationale, not restating code.
-   No hidden magic numbers; define named constants for thresholds and
    horizon.

## 4. Money and Dates

-   Store money as integer paise; convert to decimal INR only at
    presentation boundaries.
-   Never use binary floating-point for money arithmetic.
-   Validate positive amounts and sensible upper limits.
-   Use ISO date strings for business dates; handle timezone
    consistently.
-   Add tests for month boundaries, leap days, same-day payments, and
    past-due records.

## 5. Data Integrity

-   Treat posted money movements as append-only where practical.
-   Corrections should use reversal/correction events with audit
    metadata.
-   Use database transactions/batched writes for linked records.
-   Recalculate derived values from canonical records or reconcile
    aggregates regularly.
-   Never count one movement twice.
-   Never treat an unpaid bill as a cash outflow already paid.

## 6. API Rules

-   Validate all input server-side.
-   Use response DTOs; do not return raw Firestore documents
    indiscriminately.
-   Paginate list endpoints.
-   Keep error response shape consistent.
-   Use request IDs in logs.
-   Enforce business scope in repository/service access.

## 7. UI Rules

-   Reuse design tokens from `DESIGN.md`.
-   Include loading, empty, error, and success states.
-   Use accessible labels, focus states, keyboard interactions, and
    semantic controls.
-   Avoid color-only status communication; pair colors with text/icons.
-   Use Indian currency formatting and tabular numerals.
-   Confirm before reversals or other high-impact actions.
-   The UI must clearly distinguish actual, scheduled, estimated, and
    simulated values.

## 8. Testing and Delivery

-   Unit test money, ledger, forecast, and scenario calculations.
-   Add API tests for authorization and business rules.
-   Add frontend tests for core form and comparison flows.
-   Run lint, type checks, tests, and build before merge/deploy.
-   Keep seed data deterministic.
-   Update docs when routes, schema, or business rules change.
