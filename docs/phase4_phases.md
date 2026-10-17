# DukaanFlow — Phase 4 Detailed Implementation Plan

**Phase name:** Production Readiness, Reliability, Security, and Launch  
**Prerequisites:** Phase 1 and Phase 2 are stable; Phase 3 features intended for release have passed their exit criteria.  
**Primary objective:** Prepare DukaanFlow for a controlled real-world pilot by securing business data, making deployment repeatable, protecting financial integrity, improving observability and recovery, and validating the complete product end to end.

> **Release principle:** Do not call DukaanFlow production-ready merely because it deploys. A release must be secure, recoverable, testable, observable, and honest about the limits of its forecasts and integrations.

## 1. Phase 4 Scope

### Included

1. Authentication and session lifecycle suitable for a controlled pilot.
2. Business/workspace ownership and strict tenant-level data isolation.
3. Authorization checks on every API and background task.
4. Financial data integrity, audit history, idempotency, and correction workflows.
5. Firestore indexes, query efficiency, pagination, and bounded resource use.
6. Secure Google Cloud Run deployment and environment/secrets management.
7. Automated tests, CI checks, regression tests, and release gates.
8. Backups/export strategy, recovery procedures, and operational runbooks.
9. Structured logs, metrics, error reporting, health checks, and alerting.
10. Responsive UI, accessibility, loading/empty/error states, and usability polish.
11. Privacy notices, data retention/deletion process, and user support workflow.
12. Pilot release, acceptance testing, rollback plan, and post-launch review.

### Explicitly out of scope unless separately approved

- Real bank-account aggregation or automatic bank reconciliation.
- UPI payment initiation, payment collection, lending, credit scoring, or loan underwriting.
- Automatic late-fee charging or autonomous collection messages.
- Claims that a forecast guarantees future cash availability.
- Multi-region architecture, complex microservices, or enterprise infrastructure before usage justifies it.
- Treating a demo seed account as a production user account.

## 2. Release Strategy

Use three release environments where practical:

- **Development:** local development and synthetic test data.
- **Staging:** production-like configuration, synthetic or anonymized data, release-candidate testing.
- **Production/Pilot:** restricted access for approved pilot merchants; no public onboarding until the launch checklist is passed.

Promotion must be explicit: a tested commit/build is deployed to staging, accepted, and then promoted to production. Do not manually patch production code or edit production financial records to make a demo work.

## 3. Phase 4 Subphases

### Phase 4A — Production Readiness Audit and Release Scope

**Goal:** Establish what is safe to release, identify unresolved risks, and freeze a realistic launch scope.

**Tasks**

- Review `01_PRD.md`, `02_TRD.md`, `03_DATABASE_SCHEMA.md`, `04_AUTH_SECURITY.md`, `05_API_SPEC.md`, `06_ENGINEERING_RULES.md`, `07_AI_ASSISTANT.md`, `09_TESTING_DEPLOYMENT.md`, `PRODUCTION_CODING_RULES.md`, `PRODUCTION_SECURITY.md`, and Phases 1–3.
- Build a release checklist covering every feature and its owner, tests, data sensitivity, dependencies, and known limitations.
- Classify features as `release`, `pilot-only`, `feature-flagged`, or `deferred`.
- Confirm that the released forecast is deterministic and that baseline and What-If scenario calculations remain separate.
- Confirm that receivables are not counted as available cash before collection and unpaid supplier bills only reduce actual cash when paid.
- Identify any use of sample data, mock authentication, hardcoded IDs, placeholder secrets, unhandled exceptions, or unfinished UI paths.
- Create a risk register with severity, likelihood, mitigation, owner, and decision deadline.
- Set release acceptance criteria and a freeze date for non-critical feature work.

**Deliverables**

- Release scope checklist.
- Known limitations and risk register.
- Feature-flag inventory.
- Pilot acceptance checklist.

**Exit criteria**

- No critical feature has ambiguous ownership or undocumented financial behavior.
- All known high-severity issues have an owner and release decision.
- Demo-only shortcuts are either removed or safely isolated from production.

### Phase 4B — Authentication, Sessions, and Business Isolation

**Goal:** Ensure each merchant can access only the account and business data they are authorized to access.

**Tasks**

- Select and document the production authentication method. Prefer a well-supported identity provider or a carefully implemented, tested authentication flow rather than custom cryptography.
- Implement sign-in, sign-out, session expiry, refresh/session renewal if applicable, and unauthorized-session handling.
- Use secure cookie/session settings when cookies are used: `HttpOnly`, `Secure` in production, appropriate `SameSite`, and CSRF protection where relevant.
- Never store long-lived secrets or sensitive session tokens in browser local storage unless the architecture has explicitly assessed and accepted the risk.
- Define the ownership model: user, business/workspace, and membership/role. For a single-owner pilot, keep the model simple but leave the ownership boundary explicit.
- Derive the active user and permitted business IDs from verified authentication context, not from a client-supplied `business_id` alone.
- Enforce tenant isolation in every read, write, search, export, import, AI request, report, notification job, and background task.
- Check object ownership before returning or mutating a customer, supplier, bill, expense, repayment, budget, report, import batch, or notification.
- Add roles only if needed; if roles exist, define permissions in one centralized policy layer.
- Return safe `401` and `403` responses without leaking whether another business's record exists.
- Add account recovery and email/phone verification only if the chosen identity provider and pilot requirements support them safely.
- Provide a way to disable a compromised or offboarded user and revoke active sessions where supported.

**Required tests**

- User A cannot read, update, delete, export, or infer User B's records by changing IDs.
- A user cannot supply another business ID to an API and gain access.
- Unauthenticated requests cannot reach protected APIs.
- Expired or revoked sessions are rejected.
- Background tasks use the correct business scope and do not operate with a broad, unscoped query.

**Exit criteria**

- Every protected route has an authentication and authorization policy.
- Cross-tenant access tests pass for normal routes, CSV workflows, AI, notifications, and scheduled jobs.
- No demo credential or shared production login is required for ordinary use.

### Phase 4C — Financial Data Integrity and Auditability

**Goal:** Preserve accurate, explainable financial records and provide a safe way to investigate and correct mistakes.

**Tasks**

- Store monetary values using a consistent representation. Prefer integer paise or a documented decimal-safe approach; never use binary floating-point for authoritative currency arithmetic.
- Document date/time rules, business timezone handling, rounding, currency, and the meaning of every status field.
- Validate amounts, dates, references, status transitions, and business ownership at the backend boundary.
- Use server-generated IDs and timestamps where appropriate; do not trust client-supplied `created_at`, `paid_at`, or authoritative status values without validation.
- Define which operations are immutable financial events and which are editable metadata. Avoid silently overwriting a historical repayment or payment record.
- For corrections, preserve history using a reversal/correction record or a clearly auditable adjustment instead of deleting the original event without trace.
- Add audit events for important actions: create/update/void financial record, repayment entry, bill payment, import confirmation, export request where required, budget changes, user access changes, and external notification action.
- Audit events should capture actor, business, action, record type/ID, timestamp, request/correlation ID, and minimal before/after metadata where appropriate. Never record passwords, tokens, provider secrets, or unnecessary customer details.
- Add idempotency protection to operations that could be repeated by network retries, especially repayment creation, payment recording, confirmed CSV import, and notification delivery.
- Define valid state transitions for bills, repayment plans, instalments, import batches, and notifications. Reject invalid transitions rather than silently coercing them.
- Reconcile derived summaries against source records. Treat cached totals as derived and rebuildable, not as the only source of truth.
- Ensure What-If Simulator changes remain isolated from real ledger data and cannot be committed accidentally.
- Add a documented process for handling a mistaken entry, duplicate entry, partial failure, and disputed status.

**Exit criteria**

- Critical financial actions are auditable.
- Duplicate API submissions do not create duplicate financial events.
- Correction and reversal behavior is documented and tested.
- Recomputed balances, reports, and forecasts reconcile with canonical records.

### Phase 4D — Database Hardening and Performance

**Goal:** Make Firestore queries reliable, bounded, and efficient for the expected pilot workload.

**Tasks**

- Review every query for tenant scoping, expected indexes, maximum result size, and pagination behavior.
- Add and version required Firestore composite indexes; verify them in staging before production deployment.
- Avoid loading an entire collection to calculate a dashboard or report. Use bounded queries and backend aggregation logic appropriate to the data model.
- Add pagination to customer lists, ledger history, bills, expenses, notifications, and audit history where lists may grow.
- Set maximum page sizes and validate date ranges and filters.
- Review N+1 query patterns and repeated reads. Cache only non-sensitive derived information where invalidation behavior is understood.
- Define when a derived summary can be recomputed and how stale values are detected.
- Set practical request timeouts, upload limits, CSV row limits, and AI input/output limits.
- Test concurrent updates and duplicate submissions for operations that could affect balances or status.
- Document Firestore data model tradeoffs and any denormalized fields, including how they are maintained and repaired.
- Run representative load tests against staging with synthetic data rather than production customer records.
- Track slow endpoints and high-read operations; optimize based on measurements instead of premature complexity.

**Exit criteria**

- High-traffic screens use bounded queries and stable pagination.
- Required indexes are documented and deployed through a repeatable process.
- Load tests meet the team's agreed latency/error targets for pilot-scale usage.
- No critical endpoint relies on unbounded collection scans.

### Phase 4E — Google Cloud Deployment and Configuration

**Goal:** Deploy a repeatable, secure version of the app to Google Cloud Run.

**Tasks**

- Separate frontend and backend deployment responsibilities clearly. Deploy the FastAPI backend to Cloud Run; deploy the React frontend using the selected static hosting strategy or a separately managed service.
- Create separate development/staging/production projects or appropriately isolated environments where feasible.
- Configure environment-specific values through environment configuration and Secret Manager. Keep credentials out of source control, frontend bundles, build logs, and Docker image layers.
- Use a dedicated least-privilege service account for the backend rather than broad default permissions.
- Grant only required Firestore and Secret Manager permissions to that service account.
- Configure Cloud Run service settings, request timeout, concurrency, minimum/maximum instances if justified, CPU/memory, and scaling limits based on testing.
- Configure CORS to allow only the intended frontend origins per environment. Do not use wildcard origins with credentialed requests.
- Enforce HTTPS for public traffic and ensure cookies/security headers are configured for the deployment topology.
- Add health/readiness endpoints that do not disclose secrets, internal configuration, or private data.
- Add a repeatable build and deploy script or CI workflow. Pin dependencies and use reproducible build steps where practical.
- Add a documented process for deploying Firestore indexes and rules/configuration alongside code.
- Verify frontend API base URLs, allowed origins, callback URLs, and provider configuration in each environment.
- Add a production smoke test after deployment and record the build/commit version.
- Keep the previous known-good deployment available for rollback when supported by the deployment process.

**Exit criteria**

- A clean deployment can be reproduced from the repository and documented configuration.
- No secrets are embedded in frontend code or source control.
- Staging and production use separate configuration and data boundaries.
- Health checks and post-deployment smoke tests pass.

### Phase 4F — CI, Automated Testing, and Release Gates

**Goal:** Prevent regressions and block unsafe builds from reaching the pilot.

**Tasks**

- Add continuous integration for pull requests and main-branch changes.
- Run formatting, linting, static type checks, dependency checks, backend unit tests, API tests, frontend tests, and production build checks.
- Maintain deterministic unit tests for balances, partial repayments, supplier bills, overdue calculations, budgets, forecast points, and What-If scenario isolation.
- Add API integration tests for authentication, authorization, validation, pagination, idempotency, error handling, and rate limits.
- Add end-to-end tests for key workflows: create customer, record credit sale, record partial repayment, create supplier bill, record expense, review forecast, inspect alert, run a scenario, export a report, and confirm a valid CSV import.
- Test AI-enabled and AI-disabled paths. AI provider outages must not break core bookkeeping or forecast workflows.
- Add regression tests for prompt injection, untrusted CSV content, unsupported AI claims, and source-ID authorization.
- Add tests for Firestore emulator or an isolated test database where appropriate; never run destructive test fixtures against production.
- Use synthetic test fixtures and deterministic seeds so test results are reproducible.
- Add a dependency vulnerability scan and secret scan to CI. Define a process for reviewing and updating vulnerable dependencies.
- Set a minimum required test suite and branch protection/review rules suitable for the team size.
- Fail the release pipeline on critical test failures, leaked secrets, or production build errors.

**Suggested initial release gates**

- All required unit and integration tests pass.
- No known unresolved critical/high severity security finding.
- Production frontend and backend builds succeed.
- Tenant isolation and financial integrity tests pass.
- Database/index changes have been reviewed and can be deployed safely.
- Rollback and recovery instructions are current.

**Exit criteria**

- Every critical financial workflow has automated regression coverage.
- CI runs consistently and provides actionable failure output.
- Production deployment cannot proceed while mandatory release gates fail.

### Phase 4G — Observability, Error Handling, and Operational Runbooks

**Goal:** Detect failures early and give the team enough safe information to diagnose them.

**Tasks**

- Use structured backend logs with timestamp, severity, environment, service/version, route or job name, and correlation ID.
- Never log passwords, access tokens, API keys, session cookies, full sensitive prompts, or unnecessary customer/financial details.
- Add error reporting for unhandled exceptions in frontend and backend, with user-visible generic errors and detailed restricted diagnostics for operators.
- Track service-level metrics such as request count, latency, error rate, timeout rate, AI provider failures, CSV import failures, notification failures, and background job outcomes.
- Monitor Cloud Run health and resource usage, Firestore errors/latency, and unexpected cost spikes.
- Create alerts for sustained elevated error rates, repeated deployment failures, persistent provider failures, and resource/cost anomalies. Avoid noisy alerts for expected user validation errors.
- Ensure health endpoints distinguish process health from critical dependency health where appropriate.
- Provide friendly UI error states with retry guidance where retry is safe. Do not retry non-idempotent financial writes blindly.
- Create runbooks for: service outage, failed deployment, Firestore access issue, AI provider outage, stuck CSV import, duplicate transaction report, notification failure, suspected data exposure, and restore from backup.
- Define who is responsible for reviewing alerts during the pilot and how users report a problem.
- Document a support escalation path and an incident severity scale.

**Exit criteria**

- Operators can correlate a user-reported issue to backend logs without exposing sensitive data.
- Critical service and data-integrity failures have actionable alerts or documented manual checks.
- Runbooks have been tested in a staging exercise.

### Phase 4H — Backup, Recovery, and Data Lifecycle

**Goal:** Reduce the impact of accidental deletion, data corruption, or operational mistakes.

**Tasks**

- Choose and document a backup/export strategy for Firestore based on available Google Cloud capabilities and the pilot's recovery needs.
- Define recovery point objective (RPO) and recovery time objective (RTO) appropriate to a small pilot; do not claim targets until they have been tested.
- Automate scheduled backups/exports if supported by the chosen setup and verify that the job completes successfully.
- Store backups with least-privilege access and retention controls; do not make backup objects publicly accessible.
- Define retention periods for backups, logs, CSV upload files, temporary import staging data, and audit records.
- Test restoring a backup into an isolated environment and validate record counts, relationships, balances, and report reconciliation.
- Document how to recover from a bad application release versus how to recover from corrupted or deleted data; rolling back code does not automatically roll back database writes.
- Provide a data export and account/business offboarding process consistent with the product's privacy commitments and applicable requirements.
- Define a secure deletion process for temporary uploads and expired data, with any legally or operationally required retention documented.
- Keep audit records for sensitive recovery and administrative actions.

**Exit criteria**

- A backup completes and can be located by an authorized operator.
- A restore drill has been performed and recorded.
- RPO/RTO, retention, access control, and recovery limitations are documented.

### Phase 4I — Frontend Polish, Accessibility, and Usability

**Goal:** Make core workflows understandable and dependable for merchants who may not be technical.

**Tasks**

- Preserve the Merchant Flow Precision design system: light neutral canvas, white cards, subtle borders, restrained emerald/blue/amber/red semantic colors, Inter typography, and tabular numerals for currency.
- Ensure dashboard, khata, supplier bills, expenses, repayment schedules, reports, forecast, What-If Simulator, notifications, and settings work at supported desktop and mobile widths.
- Add loading, empty, validation, permission-denied, offline/network-failure, and recoverable error states for each important screen.
- Use plain language for statuses and explain terms such as receivable, payable, overdue, projected balance, and scenario.
- Show dates and currency consistently using Indian locale conventions where appropriate; avoid ambiguous date entry.
- Ensure all destructive or consequential actions have clear confirmation and context. Never use a confirmation dialog as a substitute for backend authorization.
- Clearly distinguish actual balances, expected collections/payments, deterministic forecast estimates, and hypothetical What-If scenarios in charts and labels.
- Keep the safety threshold configurable and clearly labeled; do not hardcode a universal ₹15,000 threshold.
- Check keyboard navigation, focus order, visible focus states, semantic labels, form error association, contrast, and accessible chart alternatives.
- Avoid relying on color alone to convey payment status or risk.
- Prevent double submissions with disabled/loading states while retaining server-side idempotency.
- Test realistic longer names, large amounts, empty datasets, long ledger histories, and error messages.
- Run a usability walkthrough with a person unfamiliar with the project and record points of confusion.

**Exit criteria**

- Core screens work at the agreed viewport sizes and have complete loading/empty/error states.
- Financial status and forecast assumptions are understandable without developer explanation.
- Keyboard and contrast checks pass the team's agreed accessibility checklist.

### Phase 4J — Privacy, Legal/Policy Readiness, and User Trust

**Goal:** Explain what data DukaanFlow handles and make the product's behavior transparent.

**Tasks**

- Inventory personal and financial data collected, where it is stored, which services process it, and why it is needed.
- Publish a concise privacy notice and terms/use notice appropriate to the pilot; seek qualified legal advice where needed rather than treating this checklist as legal advice.
- Explain that forecasts are estimates based on records entered and may be incomplete or wrong when data is missing or late.
- Explain AI use in plain language, including that AI-generated explanations may be imperfect and do not change authoritative ledger calculations.
- Explain which records are shared with external providers if AI or notification integrations are enabled, and minimize data sent to those providers.
- Avoid collecting unnecessary identity details, contacts, or sensitive information. Do not request UPI PINs, banking passwords, OTPs, or payment credentials.
- Define access, correction, export, retention, and deletion processes for pilot data.
- Define support contact and incident reporting instructions.
- Review consent and messaging expectations before enabling any external reminder provider.
- Document limitations: no payment execution, no guaranteed collection, no lending or credit decision, and no automatic fee collection in the current scope.

**Exit criteria**

- Users can find privacy, data handling, AI, forecast limitation, and support information.
- The team knows what data is collected and which services receive it.
- External integrations are disabled until their setup and user-facing disclosures are complete.

### Phase 4K — Staging Acceptance, Pilot, and Launch

**Goal:** Verify the release in a production-like environment and introduce it to a limited group safely.

**Tasks**

- Deploy a release candidate to staging using the production deployment process.
- Run smoke tests after every deployment and the full regression suite before pilot approval.
- Create a clean pilot business with synthetic data first; verify setup and onboarding without manual database edits.
- Test the full merchant journey from sign-in through customer ledger, repayment, supplier bill, expense, forecast, alert, What-If scenario, report export, and any enabled Phase 3 workflow.
- Verify that data from one pilot business is never visible to another business.
- Check mobile and desktop layouts, slow network behavior, expired sessions, invalid forms, provider outages, and recovery from a failed request.
- Run a backup/restore drill before storing important pilot records.
- Confirm monitoring, alert recipients, support workflow, feature flags, and rollback instructions.
- Start with a small, explicitly approved pilot cohort and a clear feedback channel.
- Collect usability feedback and issue reports without requesting unnecessary sensitive data.
- Triage issues by severity. Pause onboarding or disable a feature if a critical data-integrity or privacy issue appears.
- Keep a release note listing what changed, known limitations, and any feature flags.
- Hold a post-pilot review to decide whether to fix, extend the pilot, or open onboarding more broadly.

**Exit criteria**

- Staging acceptance checklist is signed off.
- Pilot users can complete core tasks without developer intervention.
- Rollback, backup, monitoring, and support are ready.
- No unresolved critical issue affects confidentiality, data integrity, or core financial workflows.

## 4. Recommended Implementation Order

1. **4A — Readiness audit and release scope**
2. **4B — Authentication and business isolation**
3. **4C — Financial integrity and auditability**
4. **4D — Database hardening and performance**
5. **4E — Cloud deployment and configuration**
6. **4F — CI and automated testing**
7. **4G — Observability and runbooks**
8. **4H — Backup and recovery**
9. **4I — Frontend polish and accessibility**
10. **4J — Privacy and user trust**
11. **4K — Staging acceptance and controlled pilot**

Some work can proceed in parallel, but do not start a public launch before authentication, tenant isolation, financial integrity, backup/recovery, and release-gate checks are complete.

## 5. Suggested Ownership for a Small Team

| Workstream | Suggested owner | Supporting roles |
|---|---|---|
| Authentication, API authorization, data integrity | Backend lead | Security reviewer, frontend lead |
| Frontend UX, accessibility, error states | Frontend lead | Product/test owner |
| CI/CD, Cloud Run, monitoring, backups | Deployment/DevOps owner | Backend lead |
| Test plan, regression, acceptance checklist | QA/product owner | All developers |
| Privacy text, limitations, support process | Product owner | Team reviewer; qualified advice where needed |

One person may hold multiple roles in a small team, but every workstream should have a named owner and reviewer.

## 6. Release-Critical Test Scenarios

### Security and authorization

- Unauthenticated access is rejected for all protected endpoints.
- A user cannot access another business by guessing or replacing record IDs.
- CSV import/export, AI summaries, notifications, and background tasks enforce the same tenant boundary.
- Secrets are absent from frontend bundles, logs, repository history, and build artifacts.

### Financial integrity

- Partial repayments reduce outstanding receivables correctly and do not double-count cash.
- Supplier bill creation does not reduce actual cash until a payment is recorded.
- A recorded payment affects actual cash once, even if the client retries the request.
- A What-If scenario never mutates the live ledger.
- Forecast values and report totals reconcile with canonical financial events.
- Corrections leave an audit trail and do not silently erase historical facts.

### Reliability and operations

- Provider timeouts do not break core ledger or forecast routes.
- A failed CSV import can be safely retried without duplicate records.
- A failed deployment can be rolled back using the documented process.
- A backup can be restored to an isolated environment and reconciled.
- Logs provide a correlation ID but do not reveal secrets or unnecessary customer details.

### UX and accessibility

- Core workflows work on agreed desktop/mobile sizes.
- Empty, loading, validation, network error, and permission error states are understandable.
- Keyboard navigation and visible focus work on core flows.
- Forecasts and scenarios are clearly labeled as projections/hypotheticals.

## 7. Security and Operational Rules

1. Never commit secrets or place provider credentials in frontend code.
2. Never trust client-supplied ownership, payment status, totals, or timestamps without backend validation.
3. Never expose cross-business records in error messages, search, AI context, exports, logs, or notifications.
4. Never use floating-point arithmetic for authoritative money calculations.
5. Never retry non-idempotent financial writes without idempotency protection.
6. Never silently delete or overwrite historical financial events to correct mistakes.
7. Never claim a successful deployment means the service is healthy; run smoke tests and inspect telemetry.
8. Never claim a backup is usable until a restore has been tested.
9. Never enable an external notification integration without configuration, authorization, consent/compliance review, and delivery-state handling.
10. Never represent forecast output as a guarantee or an AI explanation as the source of financial truth.
11. Keep demo data, staging data, and production pilot data separated.
12. Disable or roll back a feature if it creates a material data-integrity or privacy risk.

## 8. Definition of Done

Phase 4 is complete when:

- Authentication and authorization are enabled for the pilot.
- Tenant isolation is enforced and tested across all user-facing and background workflows.
- Financial calculations use safe currency handling and important changes are auditable.
- Duplicate submissions and retries cannot create duplicate financial events.
- Firestore queries are bounded, indexed, and tested for expected pilot scale.
- Cloud Run deployment is repeatable and environment configuration/secrets are handled securely.
- CI runs mandatory tests and blocks releases on critical failures.
- Monitoring, safe logs, alerting, incident runbooks, and support ownership are in place.
- Backups and restore procedures are documented and a restore drill succeeds.
- Core UI workflows have complete loading, empty, validation, and error states and pass basic accessibility checks.
- Privacy, AI, forecast limitations, data export/deletion, and support information are available to users.
- A staging acceptance run and controlled pilot have completed without unresolved critical security or data-integrity issues.

## 9. Phase 4 Outcome

DukaanFlow moves from a feature-complete application to a controlled, supportable pilot product. Merchants can use its ledger, repayment tracking, expenses, supplier bills, forecasts, What-If Simulator, and approved Phase 3 features with stronger protections around their data and financial history. The team can deploy, observe, recover, and improve the product without relying on manual production edits or undocumented procedures.
