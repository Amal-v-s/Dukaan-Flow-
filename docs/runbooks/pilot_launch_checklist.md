# DukaanFlow Controlled Pilot Launch & Operational Checklist

## Pre-Launch Verification Checklist
- [x] **Authentication & Sessions (4B):** JWT generation, password hashing via bcrypt, 401 unauthenticated enforcement.
- [x] **Tenant Isolation (4B):** Strict cross-tenant IDOR protection verified.
- [x] **Financial Integrity (4C):**
  - All amounts in integer paise (never float).
  - Idempotency key protection prevents duplicate credit/debit submissions.
  - Non-destructive reversing adjustments leave full audit trails.
  - Audit event logging for all financial mutations.
- [x] **Database & Repositories (4D):** Repository layer supporting Firestore and zero-dependency testing fallback.
- [x] **Live Calculations (4D):** Dashboard dynamically invokes 14-day deterministic forecast calculation without hardcoded numbers.
- [x] **Containerization & Deployment (4E):** Multi-stage non-root Dockerfile, deploy scripts, and environment configs.
- [x] **CI/CD Pipelines (4F):** GitHub Actions CI and CD workflows configured.
- [x] **Observability (4G):** Structured JSON logs with request correlation IDs and enhanced `/health/ready` probe.
- [x] **Disaster Recovery (4H):** Automated backup and restore scripts with documented RPO (24h) and RTO (2h).
- [x] **Frontend Polish & Safety (4I & 4J):**
  - React Error Boundary catching crashes with reload shortcut.
  - Indian currency comma formatting (`₹1,48,200`).
  - Privacy Notice and Terms of Service routes with clear financial and AI disclaimers.
  - Comprehensive Data Inventory documented.
- [x] **Smoke Tests (4K):** Complete merchant lifecycle test passing end-to-end.

## Sanity Verification Command
Run the complete backend test suite:
```bash
pytest -v
```
Build the production frontend bundle:
```bash
npm run build
```
Verify zero lint errors:
```bash
npm run lint
```
