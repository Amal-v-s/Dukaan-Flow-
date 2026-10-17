# DukaanFlow

DukaanFlow is a cashbook and working-capital app for small Indian merchants. It brings customer credit (khata), supplier bills, expenses, and projected cash flow into one workspace so a shop owner can see what is owed, what is due, and how upcoming movements may affect cash.

The app is designed around deterministic financial calculations: monetary values are stored as integer paise, customer and supplier records are tenant-scoped, and hypothetical simulations do not change the real ledger.

## What the app does

- **Store access:** Sign in or register a tenant-scoped business workspace, or enter the sample workspace with the one-click demo option.
- **Dashboard:** View cash position, receivables, payables, recent activity, upcoming obligations, and forecast alerts.
- **Customers and khata:** Create customer accounts, record credit sales and due dates, track outstanding balances, and record repayments or reversals.
- **Suppliers:** Record supplier bills and due dates, then track partial or full payments.
- **Transactions and expenses:** Record cashbook inflows, outflows, and categorized expenses.
- **Cash-flow forecast:** Project daily balances for the next 14 days and flag negative balances or breaches of the configured safety buffer.
- **What-If simulator:** Preview a change to an upcoming collection or bill, or add a hypothetical expense. It compares the baseline and changed forecast without saving the scenario or mutating real records.
- **Store settings:** Configure the merchant’s cash safety buffer.
- **Business management:** Track repayment plans and budgets, review date-filtered reports, manage in-app reminders, and access an audit trail through the API.
- **CSV tools:** Export supported data and validate expense imports before confirming them.
- **AI explanations (optional):** Request grounded forecast or alert explanations, business summaries, and reminder drafts. The deterministic financial calculations remain in the backend; AI is optional and does not send messages.
- **WhatsApp reminder (manual):** Open a prefilled customer reminder in WhatsApp. The shopkeeper reviews and sends it; the app does not automatically deliver messages.

## Technology stack

| Area | Technology |
| --- | --- |
| Frontend | React 19, TypeScript 6, Vite 8, Tailwind CSS 4, React Router 7, Lucide icons |
| Backend API | Python 3.11+, FastAPI, Pydantic 2, Uvicorn |
| Authentication | JWT access tokens, PyJWT, bcrypt password hashing |
| Persistence | Google Cloud Firestore via the server SDK; isolated in-memory storage when no cloud project or emulator is configured |
| Optional AI | Gemini API adapter, enabled only with a server-side API key and feature flag |
| Testing and quality | pytest, TypeScript compiler, Vite production build, oxlint |
| Hosting configuration | Firebase Hosting frontend configuration with an `/api/**` rewrite to Cloud Run |

The browser talks to the FastAPI backend. It does not connect directly to Firestore. In Firestore mode, the backend uses Google Application Default Credentials (ADC) or the Firestore emulator.

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/v1/       # FastAPI route handlers
│   │   ├── core/         # Auth, config, database, tenant context
│   │   ├── domain/       # Money, ledger, and forecast calculations
│   │   ├── repositories/ # Persistent account and business data access
│   │   ├── schemas/      # Request and response models
│   │   └── services/     # Business workflows and integrations
│   ├── tests/            # Backend tests
│   ├── .env.example      # Backend environment template
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Shared layout and UI components
│   │   ├── context/      # Authentication context
│   │   ├── features/     # Dashboard, khata, suppliers, forecast, etc.
│   │   └── lib/          # API client and formatting helpers
│   └── package.json
├── docs/                 # Product, API, architecture, security, and phase docs
├── firebase.json         # Firebase Hosting and Cloud Run rewrite config
└── package.json          # Root development and quality scripts
```

## Requirements

- Python 3.11 or newer
- Node.js 20.19+ or 22.12+
- npm
- Git

For Firestore persistence, also install the Google Cloud CLI and have access to a Google Cloud project with Firestore enabled. Local development can use in-memory storage without a cloud account.

## Local setup: in-memory mode

This is the quickest way to run the app. Data stays in process memory and is cleared when the backend stops.

1. Clone the repository and open its root directory:

   ```bash
   git clone <repository-url>
   cd Dukaan-Flow-
   ```

2. Create and activate a Python virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows PowerShell, activate it with:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

3. Install backend dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r backend/requirements.txt
   ```

4. Create the backend environment file:

   ```bash
   cp backend/.env.example backend/.env
   ```

   For in-memory mode, edit `backend/.env` and leave `GOOGLE_CLOUD_PROJECT` blank or commented out. Leave `FIRESTORE_EMULATOR_HOST` commented out. Also make sure `FIREBASE_PROJECT_ID` and `GCP_PROJECT` are not set in your shell. Do not commit `backend/.env`.

5. Install frontend dependencies:

   ```bash
   npm install --prefix frontend
   ```

6. Start the backend and frontend in separate terminals from the repository root. Activate the virtual environment in the backend terminal first.

   **Terminal 1 — backend API:**

   ```bash
   npm run dev:backend
   ```

   The API runs at `http://localhost:8000`. Interactive API documentation is at `http://localhost:8000/docs`.

   **Terminal 2 — frontend:**

   ```bash
   npm run dev:frontend
   ```

   Open `http://localhost:5173`. Vite proxies `/api` and `/health` requests to the backend on port 8000.

7. On the login page, use **Use Instant Demo Store** to enter the sample workspace. You can also register a store; a new store starts with empty business records.

Health checks are available at `http://localhost:8000/health/live` and `http://localhost:8000/health/ready`.

## Use Firestore for persistent local data

1. Create a Firestore database in your Google Cloud/Firebase project.
2. Copy `backend/.env.example` to `backend/.env` and set the project and database values:

   ```dotenv
   GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
   FIRESTORE_DATABASE_ID=(default)
   ```

3. Authenticate locally with Application Default Credentials:

   ```bash
   gcloud auth application-default login
   ```

4. Start the app using the local setup commands above.

For emulator use, start the Firestore emulator and set `FIRESTORE_EMULATOR_HOST`, for example `127.0.0.1:8080`, in `backend/.env`. Keep service-account keys and secrets out of the repository and frontend. If Firestore is configured but cannot initialize, the backend fails instead of silently switching to volatile storage.

The first authentication operation initializes the demo tenant if it is absent. New store registrations create isolated, empty business workspaces. The browser Firebase configuration/API key is not used for privileged backend database access.

## Optional Gemini explanations

AI is disabled by default. To enable it, set these values in `backend/.env`:

```dotenv
AI_FEATURES_ENABLED=true
GEMINI_API_KEY=your-server-side-key
GEMINI_MODEL=gemini-flash-latest
```

Restart the backend after changing environment settings. Keep the key on the server and never put it in frontend code. If AI is disabled or unavailable, deterministic fallback explanations are used.

## Tests and checks

Run commands from the repository root with the Python virtual environment active:

```bash
# Backend test suite
npm run test:backend

# Frontend type-check and production build
npm run build:frontend

# Frontend lint
npm --prefix frontend run lint
```

The Firestore persistence integration test requires a configured Firestore emulator; it is skipped when the emulator is unavailable. For a focused backend test, run `python -m pytest backend/tests/test_scenario_preview.py -q`.

## Deployment notes

The backend includes a Python 3.11 Dockerfile intended for Cloud Run. `firebase.json` serves the built `frontend/dist` directory and rewrites `/api/**` to a Cloud Run service named `dukaanflow-api-production` in `asia-south1`; update the service name and region to match your deployment. Deploy the backend separately, configure the frontend hosting target, and use a dedicated service account with the minimum required Firestore access. Set production secrets through a managed secret store, use a strong JWT secret, and configure allowed frontend origins before public launch.

Firestore emulator/staging verification and concurrency handling for simultaneous financial updates should be completed before production use. DukaanFlow does not connect to bank accounts, execute UPI payments, or automatically send WhatsApp/SMS messages.

## Further documentation

- [Product requirements](docs/01_PRD.md)
- [Technical requirements](docs/02_TRD.md)
- [Database schema](docs/03_DATABASE_SCHEMA.md)
- [Authentication and security](docs/04_AUTH_SECURITY.md)
- [API specification](docs/05_API_SPEC.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Testing and deployment](docs/09_TESTING_DEPLOYMENT.md)
- [Application flow](docs/APP_FLOW.md)
