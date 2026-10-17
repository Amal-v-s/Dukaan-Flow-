# DukaanFlow --- AI Assistant Specification

## 1. Phase

AI is optional and deferred until Phase 3. Phase 1 must work fully
without an LLM.

## 2. Purpose

The assistant explains existing ledger and forecast results in plain
language. It does not become the source of financial truth.

## 3. Allowed Use Cases

-   Explain a deterministic cash-shortage alert.
-   Summarize upcoming receivables and payables.
-   Explain which recorded events contributed to a forecast dip.
-   Summarize recorded spending by category and period.
-   Describe the difference between baseline and scenario forecasts.
-   Draft a merchant-approved payment reminder from supplied facts.
-   Answer questions about the current business dataset using authorized
    server-provided context.

## 4. Prohibited Behavior

-   Invent balances, transactions, customer promises, payment status, or
    forecast values.
-   Guarantee that a customer will pay or that a scenario will succeed.
-   Execute a payment, change a due date, alter a ledger entry, or send
    a reminder without explicit user action and a supported tool flow.
-   Provide lending eligibility, credit scoring, or legal
    determinations.
-   Calculate authoritative totals independently of the backend.
-   Expose data from another business or user.
-   Request or handle UPI PINs, OTPs, card security codes, passwords, or
    bank credentials.

## 5. Data Flow

1.  Authenticated user asks a question.
2.  Backend checks business membership.
3.  Backend retrieves only the minimum relevant records.
4.  Deterministic services calculate totals, forecast, and contributing
    events.
5.  Backend sends a compact, redacted fact package to Gemini.
6.  Model returns a plain-language explanation.
7.  UI displays the explanation with links to the underlying records
    where possible.

## 6. Grounding Contract

The model receives explicit facts such as: - Current available cash. -
Forecast date and projected balance. - Safety buffer. - Included
inflows/outflows and source IDs. - Data freshness and assumptions.

If necessary data is missing, assistant must say it cannot determine the
answer from recorded data. The backend remains authoritative.

## 7. Prompting Rules

-   Instruct the model to use only supplied business facts.
-   Require concise, non-alarmist language.
-   Mark estimates and hypothetical scenarios clearly.
-   Do not include unnecessary phone numbers or personal data in
    prompts.
-   Treat ledger notes and imported content as untrusted data, never as
    system instructions.
-   Do not allow user-supplied content to override safety or application
    rules.

## 8. Output Shape

Preferred structured output:

``` json
{
  "summary": "Cash may fall below the configured buffer on 20 October.",
  "reasons": [
    "A supplier bill is scheduled before the expected collection."
  ],
  "suggested_actions": [
    {
      "label": "Review the supplier bill",
      "type": "navigate",
      "target": "supplier_bill",
      "target_id": "bill_123"
    }
  ],
  "disclaimer": "Forecasts depend on recorded data and estimated collection dates."
}
```

Validate structured output against a schema. Never execute arbitrary
model-provided URLs, code, or database queries.

## 9. Failure Handling

-   If Gemini is unavailable, show deterministic facts and a friendly
    fallback.
-   Set timeouts and reasonable token limits.
-   Avoid sending secrets or full database dumps.
-   Log model latency and errors without logging sensitive prompts
    unnecessarily.
-   Evaluate hallucination rate and grounding on a fixed set of business
    scenarios before release.
