# Runbook: Deployment Rollback

## Overview
Procedure to safely rollback a broken release without downtime or data corruption.

## Backend (Cloud Run) Instant Rollback
Cloud Run keeps previous revisions immutable. You can rollback traffic within seconds:

1. **List recent revisions:**
   ```bash
   gcloud run revisions list \
     --service=dukaanflow-api-production \
     --region=asia-south1 \
     --format="table(name,active,creationTimestamp)"
   ```
2. **Direct 100% of traffic to previous revision:**
   ```bash
   gcloud run services update-traffic dukaanflow-api-production \
     --region=asia-south1 \
     --to-revisions=dukaanflow-api-production-00042-xyz=100
   ```
3. **Verify health:**
   ```bash
   curl -f https://api.dukaanflow.in/health/ready
   ```

## Frontend (Firebase Hosting) Rollback
1. **List hosting releases:**
   ```bash
   firebase hosting:releases:list
   ```
2. **Rollback to previous release:**
   ```bash
   firebase hosting:rollback
   ```
