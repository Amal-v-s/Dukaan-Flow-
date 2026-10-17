#!/usr/bin/env bash
# DukaanFlow Backend Deployment Script for Google Cloud Run
set -euo pipefail

ENVIRONMENT="${1:-staging}"
PROJECT_ID="${GCP_PROJECT_ID:-dukaanflow-${ENVIRONMENT}}"
REGION="${GCP_REGION:-asia-south1}"  # Mumbai region for Indian Kiranas
SERVICE_NAME="dukaanflow-api-${ENVIRONMENT}"
IMAGE_TAG="asia-south1-docker.pkg.dev/${PROJECT_ID}/dukaanflow/backend:$(git rev-parse --short HEAD)"

echo "=== Deploying DukaanFlow Backend to Cloud Run ==="
echo "Environment: ${ENVIRONMENT}"
echo "Project ID:  ${PROJECT_ID}"
echo "Region:      ${REGION}"
echo "Service:     ${SERVICE_NAME}"
echo "Image:       ${IMAGE_TAG}"

# Ensure Artifact Registry exists
gcloud artifacts repositories describe dukaanflow \
  --project="${PROJECT_ID}" \
  --location="${REGION}" >/dev/null 2>&1 || \
gcloud artifacts repositories create dukaanflow \
  --project="${PROJECT_ID}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="DukaanFlow Docker Repository"

# Build and submit image to Cloud Build
gcloud builds submit backend \
  --project="${PROJECT_ID}" \
  --tag="${IMAGE_TAG}"

# Deploy container image to Cloud Run
gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --image="${IMAGE_TAG}" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=10 \
  --cpu=1 \
  --memory=512Mi \
  --set-env-vars="ENVIRONMENT=${ENVIRONMENT},DEFAULT_TIMEZONE=Asia/Kolkata" \
  --set-secrets="JWT_SECRET_KEY=dukaanflow-jwt-secret:latest"

echo "=== Deployment Succeeded ==="
gcloud run services describe "${SERVICE_NAME}" --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)"
