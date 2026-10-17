# DukaanFlow --- Production Security Requirements

## 1. Security Objectives

Protect merchant financial records, prevent cross-business access,
maintain ledger integrity, and avoid misleading users about future cash
positions.

## 2. Identity and Access

-   Use a maintained identity provider or vetted authentication stack.
-   Verify identity tokens server-side.
-   Enforce business membership and role on every data operation.
-   Do not trust IDs sent by the browser without checking ownership.
-   Use least-privilege roles and dedicated service accounts.
-   Require re-authentication for sensitive account/security changes
    where supported.

## 3. Data Isolation

-   Every business-owned read/write is scoped to the authenticated
    business membership.
-   Add automated cross-tenant/IDOR tests for every resource family.
-   Avoid unrestricted collection-group queries unless business scope is
    enforced.
-   Never send one business's data to another user's AI context.
-   Use a separate dev project/database from production.

## 4. Data Protection

-   TLS for all deployed traffic.
-   At-rest protection provided by managed cloud services; review
    applicable configuration.
-   Secrets stored in Secret Manager or an equivalent secure facility.
-   No credentials or service-account keys in source control or frontend
    bundles.
-   Minimize personal data; phone number is optional unless required for
    a chosen workflow.
-   Define retention and deletion policies before onboarding real
    merchants.
-   Backups must be protected and restore-tested.

## 5. Ledger Integrity

-   Use integer paise.
-   Use transaction/batch writes for related records.
-   Record audit metadata for financial mutations.
-   Prefer reversal events over deletion of posted entries.
-   Add idempotency for retried financial operations where practical.
-   Reconcile derived totals against canonical records.
-   Prevent duplicate submissions using UI state and server-side
    idempotency where feasible.

## 6. API and Web Security

-   Strict request validation and body size limits.
-   Rate-limit authentication and sensitive write routes.
-   Restrictive CORS and secure headers.
-   CSRF controls when cookie authentication is used.
-   Prevent injection by using SDK/query APIs safely; never build unsafe
    query expressions from user input.
-   Use dependency scanning and timely patching.
-   Return generic errors with request IDs, not stack traces.

## 7. AI-Specific Security

-   Treat ledger notes, uploaded CSV cells, and user prompts as
    untrusted content.
-   Keep system instructions separate from retrieved business data.
-   Send only minimum necessary data to the model.
-   Validate model output against a schema.
-   Never execute model-proposed SQL, code, or arbitrary URLs.
-   Do not allow AI to create, update, or reverse financial records
    without a separate explicit authorized action.
-   Provide deterministic fallback behavior when AI is unavailable.

## 8. Payments, Lending, and Compliance Boundaries

-   Phase 1 does not initiate UPI transfers, access bank credentials,
    originate loans, or collect late fees.
-   Do not collect UPI PINs, OTPs, card security codes, or bank
    passwords.
-   If future features introduce lending, payment initiation, interest,
    or fees, obtain appropriate legal/compliance review and use
    authorized providers.
-   Payment reminders must be merchant-approved and must not use
    harassment, deceptive language, or unsupported claims.

## 9. Incident Readiness

Before production: - Define security contact and incident triage
owner. - Document secret rotation and credential revocation. - Define
breach assessment and notification workflow. - Monitor authentication
failures and unusual write patterns. - Verify backups and recovery
procedure. - Run access-control tests and dependency scans before
releases.
