# Dukaan-Flow-
Googel cloud hackathon project from team C minus.

## Optional Phase 3 AI

AI is disabled unless the backend process has `AI_FEATURES_ENABLED=true` and a server-side `GEMINI_API_KEY`. See `backend/.env.example` for optional settings. The app returns deterministic fallback explanations when AI is disabled or unavailable. Never add a real key to frontend configuration or commit it.

## Firestore database

The backend uses Cloud Firestore through the server SDK. Copy `backend/.env.example` to `backend/.env`, set `GOOGLE_CLOUD_PROJECT=dukaan-flow-b7928` (or your project ID), and create the Firestore database in that project. For local credentials, run `gcloud auth application-default login`; on Google Cloud, attach a dedicated service account with Firestore access. The Firebase client configuration/API key is not used for privileged backend access. The frontend does not connect directly to Firestore.

When no Google Cloud project is configured, the backend uses an isolated in-memory adapter for development/tests. Configured Firestore failures are surfaced instead of silently falling back to ephemeral storage. The first auth operation seeds the demo tenant if absent; newly registered businesses start empty and are scoped to the authenticated user's business ID.
