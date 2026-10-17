#!/usr/bin/env bash
# DukaanFlow Frontend Deployment Script (Firebase Hosting / Cloud Storage)
set -euo pipefail

ENVIRONMENT="${1:-staging}"
echo "=== Deploying DukaanFlow Frontend (${ENVIRONMENT}) ==="

cd frontend

# Build optimized production static bundle
npm ci
npm run build

# Deploy to Firebase Hosting
if command -v firebase >/dev/null 2>&1; then
  firebase deploy --only hosting
else
  echo "Firebase CLI not detected; bundle built in frontend/dist ready for static deployment."
fi

echo "=== Frontend Build & Deploy Succeeded ==="
