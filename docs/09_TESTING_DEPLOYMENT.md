# DukaanFlow --- Testing and Deployment

## 1. Testing Strategy

### Unit Tests

-   Money conversion and INR formatting boundaries.
-   Customer outstanding calculations.
-   Supplier bill remaining balance.
-   Expense/payment cash movements.
-   Forecast daily closing balance.
-   Safety-buffer and negative-balance alerts.
-   Scenario comparison without mutation of baseline records.
-   Date boundaries and timezone handling.

### API Tests

-   Valid and invalid customer creation.
-   Partial repayment updates outstanding correctly.
-   Reject overpayment under default policy.
-   Supplier bill creation and partial payment.
-   Expense creation and reversal.
-   Dashboard totals reconcile with source records.
-   Forecast includes only eligible future movements.
-   Scenario endpoints do not alter real ledger.
-   Authentication and cross-business access rejection.
-   Pagination and invalid query parameter behavior.

### Frontend Tests

-   Dashboard renders loading, error, empty, and populated states.
-   Customer form validation and repayment flow.
-   Supplier bill and expense entry.
-   Forecast warning details.
-   What-If changes update scenario results and leave baseline
    unchanged.
-   Responsive navigation and keyboard/focus behavior.

### End-to-End Demo

1.  Open seeded merchant dashboard.
2.  Open a customer with an outstanding balance.
3.  Record a partial repayment.
4.  Confirm customer balance and cash update.
5.  Open supplier bill list and record a bill/payment.
6.  View the 14-day forecast and shortage warning.
7.  Move a hypothetical collection date in the simulator.
8.  Compare baseline and scenario; confirm ledger remains unchanged.

## 2. Quality Gates

Before merging: - Format/lint passes. - Type checking passes. - Unit and
API tests pass. - Frontend production build passes. - No secrets in
repository. - Critical financial calculations covered by tests. - No
known cross-business authorization bypass.

## 3. Local Development

-   Provide `.env.example` with placeholder values only.
-   Document backend and frontend startup commands.
-   Use Firestore emulator or a dedicated development project where
    practical.
-   Seed repeatable sample data.
-   Keep a reset script limited to development/demo data.

## 4. Google Cloud Deployment

-   Create separate dev and production environments/projects.
-   Deploy FastAPI to Cloud Run.
-   Use a dedicated service account with least-privilege Firestore
    access.
-   Store secrets in Secret Manager or supported secret bindings.
-   Configure exact frontend CORS origins.
-   Use HTTPS.
-   Configure liveness/readiness health endpoints.
-   Configure logs, error reporting, and basic request metrics.
-   Set Cloud Run concurrency, scaling, and resource limits based on
    tests.
-   Deploy frontend to an appropriate static hosting target or separate
    service.

## 5. Release Checklist

-   [ ] Firestore indexes deployed.
-   [ ] Environment variables set and verified.
-   [ ] No production service uses demo seed data by default.
-   [ ] Authentication and business isolation tested.
-   [ ] Forecast calculations verified with known examples.
-   [ ] Error messages do not expose internal details.
-   [ ] Backup and restore plan defined before production use.
-   [ ] Rollback procedure documented.
-   [ ] Privacy notice and terms reviewed before real-user onboarding.
