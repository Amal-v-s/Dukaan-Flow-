# Runbook: Security & Data Exposure Incident Response

## Overview
Protocol for responding to potential security incidents, credential leaks, or tenant isolation violations.

## Immediate Containment Steps
1. **Rotate Compromised JWT Secrets:**
   - Update `dukaanflow-jwt-secret` in Google Cloud Secret Manager.
   - Force a new revision of the Cloud Run backend:
     ```bash
     gcloud run services update dukaanflow-api-production \
       --region=asia-south1 \
       --update-secrets="JWT_SECRET_KEY=dukaanflow-jwt-secret:latest"
     ```
   - *Note:* Rotating the JWT secret immediately invalidates all active sessions, forcing re-authentication.

2. **Revoke Affected User or Service Account Tokens:**
   - Temporarily disable the suspicious account by setting `is_active=False` in the users repository.
   - Invalidate any leaked GCP Service Account Keys immediately via `gcloud iam service-accounts keys delete`.

3. **Audit Trail Investigation:**
   - Query the `audit_events` collection to trace all actions taken by the actor ID or IP:
     ```bash
     # Inspect audit trail via management API or Cloud Logging
     curl -H "Authorization: Bearer ADMIN_TOKEN" \
       https://api.dukaanflow.in/api/v1/audit-events?limit=200
     ```

4. **Root Cause Analysis & Postmortem:**
   - Complete incident report within 48 hours.
   - Verify whether any cross-tenant data was exposed.
