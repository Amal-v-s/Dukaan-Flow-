# DukaanFlow --- Authentication and Application Security

## 1. Purpose

Define the minimum authentication, authorization, session, and
data-isolation controls for the MVP and the requirements for moving
toward production.

## 2. Authentication

-   Use a maintained identity provider or a well-reviewed authentication
    implementation; do not invent password cryptography.
-   For a hackathon demo, a clearly labeled seeded demo mode may be
    provided, but it must not be presented as secure production
    authentication.
-   If email/password is implemented, use a suitable password-hashing
    library with modern parameters, rate limits, reset flows, and
    verification where appropriate.
-   Never store plaintext passwords, passwords in logs, or reusable
    access tokens in local storage when a safer supported cookie flow is
    available.
-   Use short-lived access credentials and rotate/revoke refresh
    sessions when supported.
-   Require HTTPS outside local development.

## 3. Authorization and Tenant Isolation

-   Every business resource must be scoped to a business membership.
-   Backend derives the active user from verified identity claims; it
    must not trust `user_id` or `business_id` supplied by the browser as
    proof of access.
-   Check membership and role for every read/write endpoint.
-   Return 404 or a consistent access-denied response for cross-business
    object access without leaking whether an object exists.
-   Test IDOR cases by substituting IDs from another business.
-   Do not use a global admin/service account from the frontend.

## 4. Roles

MVP: - `owner`: full access to the demo business. - Optional `staff`:
can record/view allowed operational records but cannot change business
security settings. If staff roles are not implemented, keep a single
owner role and do not imply multi-role support in the UI.

## 5. Session and Browser Security

-   Prefer secure, HttpOnly, SameSite cookies for browser sessions when
    supported by the chosen identity architecture.
-   Protect cookie-authenticated state-changing endpoints against CSRF.
-   Configure CORS to exact trusted frontend origins; do not use
    wildcard origins with credentials.
-   Apply Content Security Policy and standard security headers at the
    appropriate hosting layer.
-   Avoid rendering untrusted notes or user data as raw HTML.
-   Validate file uploads if introduced later.

## 6. API Protection

-   Validate every request with Pydantic schemas.
-   Apply request size limits, pagination caps, and rate limits on
    authentication-sensitive endpoints.
-   Use idempotency keys for retry-prone payment/repayment creation
    where feasible.
-   Use centralized error handling; do not expose stack traces,
    credentials, internal paths, or database details.
-   Log request IDs and security-relevant events, not secrets or
    unnecessary customer personal data.

## 7. Secrets and Infrastructure

-   Store secrets in Secret Manager or the deployment platform's secret
    facility.
-   Use workload identity/service accounts with least privilege.
-   Never commit `.env`, service-account JSON, private keys, refresh
    tokens, or API keys.
-   Separate dev and production projects/configurations.
-   Limit Firestore IAM permissions to the required database and
    service.
-   Do not put privileged cloud credentials in frontend environment
    variables.

## 8. Financial Data Safety

-   Use integer paise for amounts and validate positive/allowed ranges.
-   Require explicit confirmation for reversal or destructive
    administrative actions.
-   Maintain audit events for financial mutations.
-   Forecasts must show assumptions and must not be represented as
    guaranteed future outcomes.
-   Do not collect or store bank credentials, UPI PINs, OTPs, or card
    security codes.
-   No lending, automatic payment, or real late-fee collection in the
    MVP.

## 9. Security Checklist

-   [ ] Authentication verified server-side.
-   [ ] Every endpoint enforces business membership.
-   [ ] Cross-business IDOR tests pass.
-   [ ] CORS is restrictive.
-   [ ] HTTPS enforced in deployed environments.
-   [ ] Secrets are not committed or exposed to frontend.
-   [ ] Inputs, amounts, dates, and IDs validated.
-   [ ] Logs contain no secrets.
-   [ ] Dependencies scanned and updated.
-   [ ] Backup/restore and incident procedures documented before
    production use.
