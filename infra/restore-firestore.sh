#!/usr/bin/env bash
# Firestore Database Restore Script
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <BACKUP_GCS_URI> [TARGET_PROJECT_ID]"
  echo "Example: $0 gs://dukaanflow-backups/firestore/2026-10-17_120000 dukaanflow-staging"
  exit 1
fi

BACKUP_URI="$1"
TARGET_PROJECT="${2:-${GCP_PROJECT_ID:-dukaanflow-staging}}"

echo "=== CAUTION: Restoring Firestore Database ==="
echo "Source Backup:  ${BACKUP_URI}"
echo "Target Project: ${TARGET_PROJECT}"
read -p "Are you sure you want to restore into ${TARGET_PROJECT}? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Restore aborted."
  exit 1
fi

gcloud firestore import "${BACKUP_URI}" \
  --project="${TARGET_PROJECT}"

echo "=== Firestore Database Restore Complete ==="
