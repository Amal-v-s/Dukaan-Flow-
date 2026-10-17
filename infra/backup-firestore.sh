#!/usr/bin/env bash
# Automated Firestore Backup Script to Google Cloud Storage
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-dukaanflow-production}"
BACKUP_BUCKET="${FIRESTORE_BACKUP_BUCKET:-gs://${PROJECT_ID}-backups}"
TIMESTAMP="$(date +%Y-%m-%d_%H%M%S)"
TARGET_URI="${BACKUP_BUCKET}/firestore/${TIMESTAMP}"

echo "=== Starting Firestore Backup ==="
echo "Project:    ${PROJECT_ID}"
echo "Target GCS: ${TARGET_URI}"

# Ensure bucket exists
gcloud storage buckets describe "${BACKUP_BUCKET}" >/dev/null 2>&1 || \
gcloud storage buckets create "${BACKUP_BUCKET}" \
  --project="${PROJECT_ID}" \
  --location=asia-south1 \
  --default-storage-class=NEARLINE

# Trigger Firestore managed export
gcloud firestore export "${TARGET_URI}" \
  --project="${PROJECT_ID}"

echo "=== Backup Successfully Completed: ${TARGET_URI} ==="
