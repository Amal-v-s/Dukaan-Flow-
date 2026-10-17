# Runbook: Service Outage Recovery

## Overview
This runbook guides on-call engineers through responding to a DukaanFlow production or staging service outage.

## Symptoms
- HTTP 500/502/503 responses returned from Cloud Run
- Frontend shows "Server unavailable" or network error banners
- Monitoring alert `CloudRunHighErrorRate` triggers

## Triage Procedure
1. **Check Cloud Run service metrics:**
   ```bash
   gcloud run services describe dukaanflow-api-production \
     --region=asia-south1 \
     --format="value(status.conditions)"
   ```
2. **Inspect recent container logs:**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
     --limit=50 \
     --format="table(timestamp,jsonPayload.message)"
   ```
3. **Verify Liveness and Readiness Probes:**
   ```bash
   curl -i https://api.dukaanflow.in/health/live
   curl -i https://api.dukaanflow.in/health/ready
   ```

## Immediate Mitigation
1. **If crash-looping on startup (bad configuration/secret):**
   - Verify Secret Manager permissions: `roles/secretmanager.secretAccessor` on service account.
   - Revert traffic to last known good revision:
     ```bash
     gcloud run services update-traffic dukaanflow-api-production \
       --region=asia-south1 \
       --to-revisions=PREVIOUS_REVISION=100
     ```
2. **If Firestore quota or connection outage:**
   - Confirm Google Cloud Status dashboard for Firestore `asia-south1`.
   - Temporary degrade non-essential features (AI features, background analytics).
