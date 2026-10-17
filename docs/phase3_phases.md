# DukaanFlow — Phase 3 Implementation Plan

**Phase name:** AI and Automation  
**Prerequisite:** Phase 1 and Phase 2 exit criteria are met. The ledger, repayment plans, budgets, reports, reminders, and deterministic forecast are stable and covered by tests.  
**Objective:** Add carefully grounded AI explanations, useful business summaries, optional forecast-based suggestions, CSV import/export, and more capable notifications—without allowing AI or automation to become the source of financial truth or silently mutate financial records.

> **Core rule:** DukaanFlow's backend remains authoritative for money, ledger entries, repayment status, budgets, reports, and forecasts. Gemini explains verified facts; it does not calculate authoritative totals or make financial changes.

## 1. Phase 3 Scope

### Included

1. Gemini-powered explanations for existing deterministic alerts and forecast results.
2. AI summaries of upcoming receivables, payables, expenses, overdue items, and baseline-versus-scenario forecasts.
3. Grounded, reviewable suggestions linked to existing records and deterministic calculations.
4. Merchant-approved drafting of payment reminders; no automatic sending by default.
5. CSV export for supported reports and records.
6. CSV import with preview, validation, duplicate detection, and explicit confirmation before writes.
7. More configurable in-app notifications and optional external delivery only if a provider is deliberately selected and configured.
8. AI/notification observability, evaluation tests, security checks, and user-facing failure states.

### Not included

- AI-generated or AI-modified authoritative balances, forecasts, or financial totals.
- Automatic payments, UPI execution, collection, lending, credit scoring, or real late-fee charging.
- Sending messages to customers without a separate explicit merchant action and a supported delivery integration.
- Unreviewed bulk imports or destructive overwrite of existing records.
- AI access to another business's records, raw database dumps, secrets, credentials, OTPs, or UPI PINs.
- Autonomous agents that can edit the ledger, move money, or contact customers without approval.
- Full accounting, tax filing, inventory management, or bank synchronization.

## 2. Phase 3 Subphases

### Phase 3A — AI Service Boundary and Configuration

**Goal:** Introduce an isolated AI service that can be disabled without breaking any core DukaanFlow workflow.

**Tasks**

- Read and follow `07_AI_ASSISTANT.md`, `ARCHITECTURE.md`, `02_TRD.md`, `04_AUTH_SECURITY.md`, and `06_ENGINEERING_RULES.md` before implementation.
- Add a backend AI service layer (for example, `backend/app/services/ai/`) rather than calling Gemini directly from React components or route handlers.
- Keep provider calls server-side. Store the Gemini/Vertex AI configuration in environment variables or Google Cloud Secret Manager; never put API keys in frontend code, source control, or client-visible configuration.
- Add a configuration switch such as `AI_FEATURES_ENABLED`. If disabled or unavailable, core ledger, forecast, reports, and simulator must continue to work.
- Define explicit request and response schemas with Pydantic. Reject unexpected fields and excessive input lengths.
- Set request timeouts, output-token limits, bounded retries, and rate limits. Do not retry indefinitely.
- Add a provider adapter so the rest of the application depends on DukaanFlow's internal interface, not provider-specific response formats.
- Send only the minimum context needed for the current request. Prefer aggregated facts and source identifiers over complete records or personal details.
- Add request correlation IDs and safe operational metrics such as latency, outcome, and token usage where available. Avoid logging full prompts, customer notes, or unnecessary personal data.

**Exit criteria**

- AI calls occur only from the authenticated backend.
- No secret is exposed to the frontend or committed to the repository.
- AI can be disabled without affecting deterministic features.
- Provider timeout, invalid response, and unavailable-provider paths return controlled errors or fallback content.

### Phase 3B — Grounded Cash-Flow and Alert Explanations

**Goal:** Explain the backend's existing financial findings in plain, concise language.

**Initial use cases**

- Explain why a deterministic cash-shortage alert was triggered.
- Explain which recorded events contribute to a projected cash dip.
- Summarize expected collections and supplier payments over a selected period.
- Explain a baseline forecast compared with a What-If scenario.
- Summarize recorded expenses by category and period using backend-calculated totals.
- Explain budget utilization or overdue schedules using current server-calculated status.

**Tasks**

- Create a backend-generated fact package for each supported use case. Include only the required values, dates, assumptions, data freshness, safety buffer, and source record IDs.
- Calculate all currency totals, percentages, overdue status, forecast points, and variance values in deterministic backend services before the AI call.
- Include explicit metadata such as `as_of_date`, `business_timezone`, `forecast_horizon`, `data_freshness`, and whether the result is a baseline or hypothetical scenario.
- Prompt Gemini to explain only the supplied facts, use calm language, label estimates as estimates, and say when the recorded data is insufficient.
- Require structured output matching a strict schema. Example fields: `summary`, `reasons`, `suggested_actions`, `disclaimer`, and `source_ids`.
- Validate that every returned source ID belongs to the supplied fact package and the active business. Drop or reject unsupported IDs and malformed output.
- Render source links from backend-validated records, not arbitrary model-provided URLs.
- Display a clear label such as **AI explanation** and keep key deterministic figures visible next to the explanation.
- Add a “Try again” action for recoverable provider failures, with rate limiting.

**Exit criteria**

- Explanations do not replace or change backend figures.
- The UI clearly distinguishes recorded facts, deterministic forecasts, and AI-written explanations.
- Missing data is acknowledged rather than guessed.
- All source links resolve only to authorized records in the current business.
- Tests confirm that fabricated IDs, numbers, URLs, and malformed structured output are not trusted.

### Phase 3C — Business Summaries and Suggested Actions

**Goal:** Turn existing reports and forecasts into a short, useful review of what the merchant may need to inspect next.

**Tasks**

- Add an optional “Business Brief” that summarizes a chosen period, such as the next 7 or 14 days, from backend-generated facts.
- Include only supported categories: upcoming customer collections, supplier bills, overdue items, expense categories, budget warnings, and forecast risk dates.
- Generate a small number of suggested actions, each linked to an existing record or a clearly identified app destination.
- Prefer review-oriented actions such as “Review the supplier bill due before the expected collection” or “Follow up on the overdue customer balance.”
- Where useful, include the deterministic reason and the record/date that supports the suggestion.
- Do not promise that an action will prevent a shortage, guarantee collection, or improve the merchant's finances.
- Keep scenario suggestions separate from actual ledger records. A suggestion must not create a payment, change a due date, or mark an item as paid.
- Add a “Refresh summary” action so the merchant can request a fresh summary after changing records.
- Show the period covered, generated time, and data-freshness notice.

**Exit criteria**

- Every suggested action is grounded in facts from the active business and links to a valid destination.
- Suggestions are informational and require merchant action.
- The summary period and freshness are visible.
- No AI-generated suggestion changes financial records by itself.

### Phase 3D — Merchant-Approved Reminder Drafts

**Goal:** Help merchants write clear payment follow-up messages without automating customer contact.

**Tasks**

- Add a “Draft reminder” action from a customer balance, repayment plan, or overdue instalment.
- Pass only the minimum verified facts needed: customer display name if appropriate, amount remaining, due date, and relevant merchant-approved context.
- Ask AI to draft a polite, concise, non-threatening reminder without inventing a promise, fee, payment status, or legal consequence.
- Let the merchant review and edit the draft before copying or sending it through any separately configured channel.
- Provide a deterministic template fallback when AI is disabled or unavailable.
- Clearly separate “Draft created” from “Message sent.” Creating a draft must never imply that it was delivered.
- Do not add automatic late fees, harassment, repeated pressure, or deceptive urgency.
- Do not send WhatsApp/SMS/email in this subphase unless a delivery provider is explicitly selected, configured, tested, and separately approved in scope.

**Exit criteria**

- Drafts are editable and require an explicit merchant action before external use.
- The draft contains no unverified financial claims.
- Provider failure still leaves a usable template option.
- No message is sent as a side effect of opening a customer record or generating a draft.

### Phase 3E — CSV Export

**Goal:** Let merchants download useful business data in a portable, reviewable format.

**Initial export targets**

- Customer ledger entries and receivable summaries.
- Supplier bills and recorded supplier payments.
- Expenses and category totals.
- Repayment plans and instalment status.
- Budget summaries and report outputs.

**Tasks**

- Define a separate, versioned CSV column specification for each export type.
- Apply business authorization and filters on the server before generating a file.
- Use consistent date formats, UTF-8 encoding, and documented currency representation. If amounts are exported in rupees, use clear column names; if stored in paise, convert consistently and document the conversion.
- Include stable record IDs where appropriate so exported rows can be reconciled without exposing internal secrets.
- Add date-range and status filters where meaningful.
- Prevent spreadsheet formula injection by safely escaping cells that begin with formula-triggering characters such as `=`, `+`, `-`, or `@` when exported for spreadsheet use.
- Set a reasonable row/file-size limit for the first version. For larger exports, use a controlled asynchronous job only if required.
- Return a clear error when no records match the filter; do not silently export a misleading empty report.
- Do not include authentication tokens, secrets, or unrelated personal information.

**Exit criteria**

- Exported totals and rows reconcile with the relevant in-app report.
- Cross-business export access is impossible and tested.
- CSV opens correctly in common spreadsheet tools and formula-injection tests pass.
- Export columns and formatting are documented.

### Phase 3F — Safe CSV Import and Reconciliation

**Goal:** Reduce manual entry while ensuring imported data cannot silently corrupt the ledger.

**Initial import targets**

- Expense records.
- Supplier bills, if the import schema can distinguish a bill from a payment.
- Customer ledger entries only after the team has defined reliable direction, amount, date, customer matching, and opening-balance rules.

**Tasks**

- Publish downloadable sample templates with required columns, optional columns, accepted date formats, currency rules, and examples.
- Upload to a temporary import workflow; do not immediately write every uploaded row to the live ledger.
- Validate file type, encoding, header names, row count, file size, required fields, date ranges, positive amounts, category values, and linked customer/supplier references.
- Normalize dates and amounts in a single backend import parser. Avoid locale-ambiguous values such as `01/02/2026` unless the chosen format is explicitly documented.
- Show a preview with valid rows, invalid rows, warnings, and a downloadable error report containing row numbers and explanations.
- Detect likely duplicates using a documented key or matching strategy. Treat duplicate detection as a warning unless the match is certain; never silently discard ambiguous records.
- Require the merchant to review the preview and explicitly confirm the import.
- Use an import batch ID and idempotency strategy so retrying a request cannot create duplicate financial entries.
- Persist import provenance, such as batch ID, original filename, import timestamp, and row number, without storing the file longer than needed.
- Make invalid rows non-importable until corrected. Never coerce malformed values into zero or guess missing amounts.
- Define rollback/correction behavior before enabling bulk writes. If full transactional rollback is not practical, use a staged batch and a clear compensating-action strategy.
- For customer-ledger imports, prevent imported records from being counted twice as both opening balances and individual transactions.

**Exit criteria**

- No live ledger write occurs before explicit confirmation.
- Invalid rows are clearly identified and cannot be imported accidentally.
- Retrying the same confirmed batch does not duplicate records.
- Imported totals reconcile with the preview and resulting ledger.
- Tests cover duplicate rows, malformed dates, invalid amounts, unknown linked IDs, partial failures, and repeated confirmation.

### Phase 3G — Advanced Notifications and Delivery Boundary

**Goal:** Make reminders more configurable and dependable while keeping external communication opt-in and auditable.

**Tasks**

- Extend in-app reminders with preferences such as lead time, reminder category, quiet hours, and read/acknowledged state where supported.
- Deduplicate reminders by business, source record, reminder type, and relevant due-date window.
- Generate notifications from canonical backend status, not from AI text.
- Add a notification delivery interface that can support an external provider later without coupling business logic to one vendor.
- If external delivery is approved, require explicit merchant configuration, verified sender/provider credentials, recipient validation, consent/compliance review, rate limits, and delivery-status handling.
- Keep the default Phase 3 behavior in-app only unless external delivery is deliberately configured and tested.
- Record delivery attempts and outcomes with minimal necessary metadata. Never log provider secrets or message content unnecessarily.
- Make retries bounded and idempotent so a transient failure does not send the same reminder repeatedly.
- Distinguish queued, sent, delivered, failed, and acknowledged states where the provider actually supports those states. Do not claim delivery based only on a successful API request.
- Ensure notification content does not expose another business's data and does not reveal sensitive customer details on shared screens by default.

**Exit criteria**

- Notification generation is idempotent and respects configured preferences.
- In-app notifications continue working when external delivery is not configured.
- External delivery, if enabled, has explicit configuration, bounded retries, auditability, and failure handling.
- No AI-generated content is sent without merchant review and approval.

### Phase 3H — Evaluation, Security, UX, and Release

**Goal:** Prove that AI and import/export features are grounded, safe, and dependable before release.

**Tasks**

- Build a fixed evaluation set covering cash shortages, delayed collections, supplier payments, overdue instalments, budget thresholds, missing data, stale data, and baseline-versus-scenario comparisons.
- Include adversarial ledger notes and CSV cells that attempt to instruct the model to ignore application rules or expose data. Treat all imported text and notes as untrusted data.
- Evaluate whether explanations preserve supplied amounts/dates, avoid unsupported claims, cite valid source records, and acknowledge uncertainty.
- Add tests for provider timeout, rate limits, malformed model output, prompt-injection attempts, unauthorized business IDs, invalid source IDs, and missing records.
- Add import/export security tests, including formula injection, oversized files, invalid encoding, duplicate batches, and cross-business access.
- Review the UI for loading, disabled, empty, error, retry, and confirmation states. Make AI features visibly optional.
- Ensure core workflows remain usable without network access to Gemini, subject to the app's normal backend requirements.
- Update `07_AI_ASSISTANT.md`, `05_API_SPEC.md`, `03_DATABASE_SCHEMA.md`, `ARCHITECTURE.md`, `APP_FLOW.md`, `09_TESTING_DEPLOYMENT.md`, and `DELIVERY_ROADMAP.md` as applicable.
- Run Phase 1 and Phase 2 regression tests, then run an end-to-end workflow covering forecast alert → explanation → review suggested action → draft reminder, plus CSV preview → confirmation → reconciliation.
- Document known limitations and the exact features enabled in the demo/deployment environment.

**Exit criteria**

- No critical or high-severity cross-business access or data-integrity defect remains open.
- Core deterministic features pass their regression suite with AI disabled.
- AI evaluation meets the team's documented acceptance thresholds; unsupported facts are rejected or safely handled.
- Import/export and notification tests pass.
- The demo can be completed using seeded data and configured credentials without manual database edits.

## 3. Suggested Data Model Additions

Reconcile these proposals with `03_DATABASE_SCHEMA.md` before implementation. Do not create a second source of truth for financial facts.

### `ai_interaction_logs` (metadata only)

Suggested fields:

- `business_id`
- `user_id`
- `use_case`
- `request_id`
- `status`: `succeeded`, `fallback`, `failed`
- `provider`
- `latency_ms`
- `created_at`
- Optional token/usage metadata if available and safe to retain

Avoid storing complete prompts and model outputs by default. If product requirements call for retained history, define retention, access controls, and redaction first.

### `import_batches`

Suggested fields:

- `business_id`
- `created_by`
- `import_type`
- `status`: `uploaded`, `validated`, `awaiting_confirmation`, `processing`, `completed`, `completed_with_errors`, `failed`, `cancelled`
- `file_name` (sanitized display name only)
- `file_hash` or equivalent duplicate-batch fingerprint
- `row_count`, `valid_row_count`, `invalid_row_count`
- `created_at`, `confirmed_at`, `completed_at`
- `error_summary` or a protected error-report reference

### `import_rows` or temporary staged rows

Suggested fields:

- `batch_id`
- `row_number`
- `normalized_payload` (only required fields, access-controlled, temporary if possible)
- `validation_status`
- `validation_errors`
- `duplicate_match_id` where applicable
- `created_record_id` after successful import

Use a clear retention/deletion policy for uploaded files and staged rows.

### `notification_preferences`

Suggested fields:

- `business_id` and/or `user_id`, depending on whether preferences are business-wide or per-user
- `enabled_categories`
- `lead_time_rules`
- `quiet_hours` and business timezone
- `updated_at`

### `notification_deliveries` (only if external delivery is enabled)

Suggested fields:

- `business_id`
- `notification_id`
- `provider`
- `status`
- `attempt_count`
- `provider_message_id` if safe and supported
- `last_attempt_at`, `sent_at`, `failed_at`
- Sanitized failure code/message

Keep provider credentials in secret storage, never in these documents.

## 4. Suggested API Additions

Exact routes and payloads must be reconciled with `05_API_SPEC.md` and the existing API version.

### AI explanations and summaries

- `POST /api/v1/ai/explain-alert`
- `POST /api/v1/ai/explain-forecast`
- `POST /api/v1/ai/summarize-business`
- `POST /api/v1/ai/draft-reminder`

These endpoints should accept a use-case identifier and authorized source IDs or a bounded period—not arbitrary database queries. The backend must re-fetch and authorize all referenced records and calculate facts itself.

### CSV export/import

- `POST /api/v1/exports` or narrowly scoped report export endpoints
- `POST /api/v1/imports` to create an upload/import batch
- `GET /api/v1/imports/{batch_id}` to inspect validation and processing status
- `GET /api/v1/imports/{batch_id}/errors` to download a protected error report
- `POST /api/v1/imports/{batch_id}/confirm` to confirm a validated batch
- `POST /api/v1/imports/{batch_id}/cancel` where cancellation is supported

Use the application's existing upload mechanism and limits. Do not accept arbitrary file paths or client-supplied storage locations as trusted input.

### Notifications

- `GET /api/v1/notification-preferences`
- `PATCH /api/v1/notification-preferences`
- Existing reminder endpoints from Phase 2 may be extended rather than duplicated.
- Provider-specific delivery endpoints should be internal service operations, not exposed as unrestricted user-controlled actions.

Every endpoint requires authentication, active-business authorization, validation of linked IDs, and appropriate rate/file-size limits.

## 5. Frontend Requirements

- Add AI explanation panels to relevant alerts, forecast, report, and simulator views; do not make the user leave the financial context to understand an explanation.
- Show an explicit AI label, generated time, data period, and forecast disclaimer where relevant.
- Keep actual recorded values and deterministic projections visually distinct from generated prose.
- Provide graceful fallback text when AI is disabled or fails.
- Add CSV import wizard steps: **Choose file → Map/validate columns → Preview → Confirm → Result**.
- Show row counts and validation errors before confirmation; require a separate confirmation action for financial writes.
- Add export actions to supported report/list screens and clearly indicate the selected filters and period.
- Add notification preference controls with clear defaults and timezone-aware descriptions.
- Maintain the existing minimal DukaanFlow design system, responsive layout, keyboard accessibility, and clear loading/empty/error states.

## 6. Financial Integrity and Security Rules

1. Store money using the existing integer paise convention. Do not let the model calculate or persist authoritative monetary values.
2. All forecast and report calculations remain deterministic backend functions.
3. Re-authorize every source record ID against the active business before building AI context or exporting/importing data.
4. Treat customer notes, supplier descriptions, imported CSV cells, and model output as untrusted input.
5. Never execute model-generated code, SQL, database paths, arbitrary URLs, or tools.
6. Do not allow an AI response to directly create, edit, delete, or mark financial records as paid.
7. Use idempotency keys or batch-level deduplication for imports and notification delivery.
8. Validate imported amounts, dates, categories, record references, and row limits on the server.
9. Keep secrets in server-side configuration/secret storage and redact sensitive logs.
10. Do not log full financial prompts or CSV contents unless a reviewed requirement and retention policy explicitly permits it.
11. Never imply that a reminder draft was sent, that a provider accepted a message means it was delivered, or that a forecast is guaranteed.
12. Maintain audit events for confirmed financial imports and any external notification action.

## 7. Testing Matrix

### AI grounding and behavior

- Explanation uses supplied forecast figures without changing them.
- Model output that invents a customer, amount, date, source ID, or URL is rejected or safely omitted.
- Missing/stale data is identified in the explanation.
- A baseline forecast and a What-If scenario are not conflated.
- Provider timeout, invalid JSON, rate limiting, and unavailable service trigger fallback behavior.
- Prompt-injection text inside ledger notes or CSV cells cannot override system rules.
- A user cannot request or infer another business's data through AI.
- Disabling AI leaves all core workflows functional.

### CSV export

- Export rows and totals match the filtered in-app report.
- Date and currency formats are consistent and documented.
- Formula-like values are safely escaped.
- Unauthorized business IDs cannot be exported.
- Empty results and oversized requests return clear outcomes.

### CSV import

- Valid template imports successfully after confirmation.
- Missing columns, malformed dates, invalid amounts, unknown categories, and unknown linked IDs are reported by row.
- Duplicate rows and repeated batch confirmation do not create duplicate financial records.
- Partial processing failures are visible and recoverable under the documented strategy.
- Preview totals match final imported totals.
- Import provenance links each created record to its batch where appropriate.

### Notifications

- Preferences and quiet hours are respected.
- Repeated scheduler runs do not create duplicate reminders or duplicate external sends.
- Failed delivery uses bounded retry behavior.
- Acknowledging a reminder does not change the underlying debt or bill.
- Message drafts are never sent without explicit approval.

### End-to-end regression

- Seed customer debt, repayment schedules, supplier bills, expenses, and budgets.
- Generate a deterministic 14-day forecast and a shortage alert.
- Request an AI explanation and verify its sources.
- Compare a baseline with a What-If scenario.
- Generate and edit a reminder draft without sending it.
- Export a report and reconcile totals.
- Import a valid CSV through preview and confirmation, then reconcile the ledger.
- Repeat key flows with AI disabled.

## 8. Recommended Implementation Order

1. **3A — AI boundary and configuration**
2. **3B — Grounded explanations**
3. **3C — Business summaries and suggested actions**
4. **3D — Reminder drafts**
5. **3E — CSV export**
6. **3F — CSV import and reconciliation**
7. **3G — Advanced notifications**
8. **3H — Evaluation, security, UX, and release**

If time is limited, complete and test AI explanations plus CSV export before starting more complex import or external notification work. Do not sacrifice data-integrity checks to add more AI features.

## 9. Definition of Done

Phase 3 is complete when:

- AI features are optional and isolated behind a backend service boundary.
- AI explanations and summaries are grounded in server-calculated facts and validated source IDs.
- Suggested actions are informational and do not mutate financial data.
- Reminder drafts require merchant review and explicit action before external use.
- CSV export is authorized, documented, reconciled, and protected against spreadsheet formula injection.
- CSV import uses validation, preview, explicit confirmation, deduplication, and a documented failure-recovery strategy.
- Notifications are idempotent, configurable, and honest about delivery status.
- Tests cover grounding, prompt injection, tenant isolation, import/export, notification retries, and Phase 1/2 regression.
- Documentation and deployment configuration are updated, and the demo runs without manual database editing.

**Phase 3 outcome:** DukaanFlow moves from a reliable bookkeeping and forecasting tool to an explainable, assisted workflow—while keeping the merchant in control and preserving deterministic financial truth.
