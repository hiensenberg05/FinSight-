# FinSight --- Testing Strategy and Quality Plan

**Document:** `test.md`\
**Status:** Proposed testing specification\
**Scope:** Frontend, backend, database, ingestion, financial
correctness, voice, ML, integrations, security and deployment

------------------------------------------------------------------------

## 1. Testing objectives

Testing must establish that FinSight:

1.  Imports supported CSV formats correctly and safely.
2.  Produces mathematically correct financial results.
3.  Never mixes data across users.
4.  Correctly distinguishes expenses, income, transfers, refunds and
    reversals.
5.  Routes natural-language questions to the correct financial tools.
6.  Uses Gnani STT/TTS without exposing provider credentials.
7.  Handles voice sessions, streaming, interruption and disconnects
    safely.
8.  Produces evaluated forecasts and explainable anomaly indicators.
9.  Delivers reliable notifications and Slack interactions.
10. Remains observable and recoverable under expected hackathon demo
    loads.

The system must prefer a clear failure or clarification over a
fabricated financial answer.

------------------------------------------------------------------------

## 2. Test strategy and test pyramid

``` mermaid
flowchart TB
    E2E[End-to-End Tests: critical user journeys]
    INT[Integration Tests: API, DB, providers, queues]
    UNIT[Unit Tests: domain rules, parsers, calculations]
    STATIC[Static Checks: lint, typing, migrations, build]

    E2E --> INT
    INT --> UNIT
    UNIT --> STATIC
```

### 2.1 Unit tests

Fast, isolated tests for: - Money conversion and rounding. - Date-range
interpretation. - CSV parsing and mapping. - Transaction
normalization. - Merchant matching. - Category rules. - Transfer/refund
semantics. - Budget calculations. - Savings-goal calculations. - Anomaly
features and rules. - Forecast transformations. - Tool schema
validation. - Session state transitions.

### 2.2 Integration tests

Test real boundaries using isolated dependencies: - FastAPI routes with
test database. - SQLAlchemy repositories and migrations. - CSV
upload-to-import pipeline. - Voice orchestration with mocked Gnani/LLM
providers. - Slack signature verification and event deduplication. -
Worker/job state transitions if a queue is introduced. - Private file
storage access controls.

### 2.3 End-to-end tests

Validate critical user journeys through the browser: - Sign in and view
dashboard. - Upload a CSV and confirm import. - Inspect transactions and
category summaries. - Ask a financial question using text. - Ask the
same question through voice. - Create a budget and inspect
utilization. - Review an anomaly. - Generate and download a report. -
Use Slack after linking an account.

### 2.4 Non-functional tests

-   Security and authorization.
-   Performance and concurrency.
-   Resilience and provider failure.
-   Accessibility and responsive behavior.
-   Observability and auditability.
-   Privacy and data retention.

------------------------------------------------------------------------

## 3. Test environments and data

### 3.1 Environments

  -----------------------------------------------------------------------
  Environment             Purpose                 External providers
  ----------------------- ----------------------- -----------------------
  Local development       Fast iteration          Mock by default;
                                                  optional manual smoke
                                                  tests

  CI                      Repeatable automated    No real provider calls
                          validation              by default

  Integration/staging     Validate provider and   Dedicated test
                          deployment behavior     credentials

  Demo                    Stable hackathon        Controlled seeded
                          walkthrough             synthetic dataset
  -----------------------------------------------------------------------

### 3.2 Test data

Use generated synthetic records only.

Recommended fixtures: - Small unit fixture: 20--100 transactions. -
Import fixture: each supported CSV layout. - Primary integration user:
500--800 transactions. - Full synthetic dataset: 15K--20K transactions
across 20 users and 12 months. - Anomaly ground truth: 200--300 labelled
cases. - Voice evaluation set: 100--150 prompts.

The data generator must be deterministic by seed and must not use real
customer data.

### 3.3 Test isolation

-   Use a dedicated test database or transaction-isolated schema.
-   Reset database state between test cases or use factories with
    explicit cleanup.
-   Mock time where period-boundary logic is tested.
-   Mock external provider calls in normal CI.
-   Never use production API keys in local tests or CI.
-   Do not let tests depend on execution order.

------------------------------------------------------------------------

## 4. Backend unit test plan

### 4.1 Money and currency

Test: - INR rupee-to-paise conversion. - Zero and negative amounts. -
Decimal parsing and rounding policy. - Currency exponent handling. -
Unsupported currency behavior. - Overflow boundaries for BIGINT. -
Aggregation without float conversion.

Acceptance: - Monetary values remain exact through parsing, persistence,
retrieval and aggregation. - A ₹123.45 amount is represented as 12345
INR minor units. - Invalid precision is rejected or handled according to
an explicit rounding policy. - No financial calculation uses binary
float as its source of truth.

### 4.2 Date and period logic

Test: - Calendar month boundaries. - Previous month across year
boundaries. - Leap years. - User timezone conversion. - Date-only
statement rows. - Inclusive/exclusive interval semantics. - Empty and
future date ranges. - Month-to-date versus previous full month.

Acceptance: - Every period is resolved to explicit start/end dates
before querying. - Timezone interpretation is consistent. - No
off-by-one errors at month boundaries.

### 4.3 Transaction semantics

Test: - Positive income. - Negative expense. - Transfer out and transfer
in. - Refund. - Reversal. - Fee and interest. - Unknown transaction
type. - Excluded/reviewed transaction. - Multiple currencies.

Acceptance: - Internal transfers are excluded from consumption totals. -
Refunds reduce net spending according to the documented reporting
policy. - Income and expenses are not inferred solely from sign. - Mixed
currencies are not summed without conversion rules.

### 4.4 Budget and goal calculations

Test: - Budget utilization at 0%, below threshold, exactly threshold and
over 100%. - Refund treatment. - Transfer exclusion. - Category and
total budgets. - Overlapping budget periods. - Savings goal progress. -
Zero remaining days. - Goal target already achieved. - User-entered
versus transaction-derived balances.

Acceptance: - Budget actuals can be reproduced from underlying
transaction IDs and policy. - Percentages use exact/controlled
arithmetic and defined rounding. - A goal simulation clearly states
assumptions.

### 4.5 Tool registry

Test: - Unknown tool rejected. - Invalid JSON rejected. - Missing
required fields rejected. - Extra fields handled according to strict
schema policy. - Date range maximum enforced. - Pagination/row limits
enforced. - User identity comes from authenticated context. - Tool
output schema validated. - Tool timeout and exception translated to safe
errors.

Acceptance: - The model cannot call arbitrary Python functions or
execute SQL. - The model cannot select a different user by supplying a
`user_id`.

------------------------------------------------------------------------

## 5. CSV ingestion test plan

### 5.1 Format coverage

Create fixtures for: 1. Separate debit and credit columns. 2. Signed
amount column. 3. Amount plus DR/CR indicator. 4. Different date
formats. 5. Optional running balance. 6. Extra unknown columns. 7.
Reordered columns. 8. Quoted commas and escaped quotes. 9. UTF-8 and
supported alternate encodings. 10. Empty file and header-only file.

### 5.2 Validation tests

-   Unsupported extension.
-   Oversized file.
-   Too many rows.
-   Malformed CSV.
-   Missing required columns.
-   Invalid date.
-   Ambiguous date.
-   Non-numeric amount.
-   Missing currency where required.
-   Conflicting debit and credit values.
-   Duplicate source rows.
-   Formula-like cells.
-   Unexpected null bytes or invalid encoding.
-   Extremely long cell values.

### 5.3 Normalization tests

-   Debit becomes negative amount.
-   Credit becomes positive amount.
-   DR/CR indicator is applied correctly.
-   Merchant alias resolves consistently.
-   Original description is preserved.
-   Payment mode is only set when evidence supports it.
-   Category confidence and source are recorded.
-   Transfer candidates are not treated as expenses.
-   Refunds and reversals are classified distinctly.
-   Source import ID and row number are retained.

### 5.4 Import idempotency and atomicity

Test: - Same upload submitted twice with same idempotency key. - Same
file uploaded under a new import attempt. - Retry after worker crash. -
Database failure halfway through a batch. - User cancels before
commit. - User confirms after preview. - Duplicate rows within one
file. - Duplicate import of the same statement.

Acceptance: - A retry does not create duplicate transactions. - Partial
imports are either rolled back or have an explicit resumable state. -
Every committed transaction can be traced to its source. - Invalid rows
are reported without corrupting valid rows.

------------------------------------------------------------------------

## 6. Financial analytics correctness tests

Create hand-calculated fixtures with known expected answers.

### 6.1 Core metrics

Test: - Total income. - Total expense. - Net cash flow. - Category
totals. - Merchant totals. - Average monthly spend. - Savings ratio. -
Payment-mode totals. - Period-over-period differences and percentages. -
Top-N merchant ranking.

### 6.2 Required invariants

For a selected user, period and currency: - Sum of category expense
totals must reconcile to eligible expense total, subject to explicitly
excluded/uncategorized rows. - Income minus eligible expenses must equal
net cash flow under the chosen sign/reporting convention. - Internal
transfers must not change consumption totals. - Refund treatment must be
consistent across category, merchant and period reports. - Dashboard and
voice tool results for identical parameters must match. - Results must
be stable for identical database state and query parameters.

### 6.3 Cross-user tests

Create User A and User B with overlapping dates, amounts and merchants.

Verify: - A cannot retrieve B's transactions. - A cannot see B's
category totals. - A cannot access B's imports, reports, goals or
anomalies. - A cannot use a guessed UUID to access B's resources. -
Voice and Slack tools enforce the same ownership boundary.

------------------------------------------------------------------------

## 7. Voice and conversational testing

### 7.1 Provider adapter tests

Mock provider responses for: - Successful STT. - Empty transcript. -
Multiple transcript segments. - Unsupported language. - Authentication
failure. - Rate limit. - Provider timeout. - Malformed response. -
Connection reset. - Partial stream followed by disconnect. - TTS audio
chunks. - TTS failure after partial output.

Adapter tests must verify parsing and translation to provider-neutral
internal events.

### 7.2 Voice session lifecycle

Test: - Authenticated session start. - Unauthenticated session
rejected. - Audio before session ready. - Invalid audio frame. -
Oversized audio payload. - Concurrent turns. - User interruption. -
Request cancellation. - Browser disconnect. - Provider disconnect. -
Idle session expiration. - Cleanup after failure. - Late provider event
from superseded request. - Reconnect behavior.

Acceptance: - A request ID identifies each turn. - Superseded output is
not played as the current answer. - Session resources are released. -
One user's session cannot be attached to another user's connection.

### 7.3 Language and code-mix evaluation

Include English, Hindi and Hinglish prompts where supported by the
selected Gnani configuration. Add other Indic languages only after
verifying account/model support.

Evaluate: - Transcription correctness. - Language identification. -
Merchant names and common financial vocabulary. - Currency amounts. -
Dates and periods. - Code-mixed utterances. - Accent/noise robustness on
a controlled sample.

Track word error rate or task-specific entity accuracy where reference
transcripts are available. Do not judge STT solely by whether the
transcript sounds plausible.

### 7.4 Intent and tool-selection evaluation

For each voice prompt, measure: - Correct intent. - Correct tool. -
Correct date period. - Correct category/merchant. - Correct currency. -
Correct clarification behavior. - Correct refusal for unsupported
requests.

Example cases: - "How much did I spend on food last month?" - "Compare
this month with the previous one." - "Which merchant gets most of my
money?" - "Find duplicate-looking transactions." - "Can I save ₹50,000
in six months?" - "How much did I spend through UPI?" - Ambiguous: "What
about last time?" - Unsupported: "Transfer ₹10,000 to my friend."

The unsupported transfer request must not trigger a financial mutation.

### 7.5 Response correctness

Compare spoken/text response claims against the tool result: - Amount. -
Currency. - Period. - Category. - Merchant. - Forecast status and
assumptions. - Anomaly wording.

The response must not claim fraud, certainty or unsupported causal
explanations.

### 7.6 End-to-end voice latency

Measure: - Audio capture completion. - STT first/final transcript. -
Reasoning duration. - Tool execution. - TTS first audio. - Total turn
time.

Report p50 and p95 under a documented test environment. Do not define
targets before collecting a baseline.

------------------------------------------------------------------------

## 8. Anomaly detection tests

### 8.1 Rule-level tests

-   Large amount relative to user/category baseline.
-   Category spending spike.
-   Merchant frequency change.
-   Duplicate candidate with same amount/date/merchant.
-   Similar transactions that are legitimate recurring payments.
-   Refund and reversal not incorrectly flagged as expenses.
-   New user with insufficient baseline history.

### 8.2 Evaluation

Use labelled synthetic anomaly cases and benign hard negatives.

Report: - Precision. - Recall. - F1. - False-positive rate. -
Performance by anomaly type. - Coverage/abstention for insufficient
history.

Acceptance: - Detector output includes explainable evidence. -
Model/detector version is stored. - Anomaly is not described as proven
fraud. - User review outcome can be recorded.

------------------------------------------------------------------------

## 9. Forecasting tests

### 9.1 Baselines

Compare proposed models against: - Last-month baseline. - Moving-average
baseline. - Seasonal-naive baseline when sufficient history exists.

### 9.2 Evaluation design

-   Chronological train/validation/test split.
-   Example: first 9 months train, next 3 months holdout.
-   No random transaction-level split for time-series forecasting.
-   No future leakage in feature construction or preprocessing.
-   Evaluate at the same aggregation level as the product output.

### 9.3 Metrics

Use suitable metrics such as: - MAE. - RMSE. - WAPE or MAPE only where
denominators make sense. - Interval coverage if prediction intervals are
produced.

Acceptance: - Forecast output records training window and model
version. - Insufficient history returns an explicit status. - Forecasts
are labelled estimates. - Forecasts are compared with a baseline before
being presented as useful.

------------------------------------------------------------------------

## 10. Frontend tests

### 10.1 Component tests

-   Upload component: file selection, validation and progress.
-   Dashboard: loading, empty and error states.
-   Charts: correct labels, currency and period.
-   Transaction table: pagination and filtering.
-   Budget UI: utilization and threshold display.
-   Goal UI: target and progress.
-   Anomaly review: confirm/dismiss state.
-   Voice UI: permission, recording, playback, stop and error state.

### 10.2 Accessibility and responsive tests

-   Keyboard navigation.
-   Accessible names and labels.
-   Focus management in dialogs.
-   Color contrast.
-   Screen-reader status for voice state.
-   Reduced motion.
-   Mobile and desktop layout.
-   Microphone permission denied.
-   Unsupported browser audio capability.

### 10.3 Frontend security checks

-   No API keys in built JavaScript.
-   No sensitive transaction data in URLs.
-   Logout clears user-scoped cached data.
-   Switching users does not display stale cached data.
-   Protected pages enforce authenticated state.

------------------------------------------------------------------------

## 11. Slack integration tests

-   Valid Slack signature.
-   Invalid signature rejected.
-   Stale/replayed request rejected where applicable.
-   Duplicate event ID processed once.
-   Unlinked Slack user denied financial access.
-   Linked Slack identity maps to correct FinSight user.
-   Revoked link denied.
-   Bot token never appears in logs.
-   Tool errors return safe user-facing messages.
-   Slack message retries do not duplicate notifications or mutations.

------------------------------------------------------------------------

## 12. Security and privacy testing

### 12.1 Authorization

-   Cross-user IDOR tests for every user-owned endpoint.
-   Voice session ownership tests.
-   Report download ownership tests.
-   Import file ownership tests.
-   Slack identity mapping tests.
-   Background job owner checks.

### 12.2 Input and file security

-   CSV formula injection.
-   Path traversal in filenames.
-   Oversized request and decompression limits where relevant.
-   Malformed JSON.
-   SQL injection attempts in merchant descriptions and filters.
-   Prompt injection text embedded in transaction descriptions.
-   HTML/script content in merchant names and notes.
-   Unsafe report download names.

### 12.3 Secrets and logs

-   Search repository and built artifacts for credentials.
-   Ensure authorization headers are redacted.
-   Ensure stack traces do not expose tokens.
-   Ensure raw statement rows are not logged.
-   Ensure voice transcript logging follows retention policy.
-   Ensure debug mode is disabled in deployed environments.

### 12.4 LLM tool safety

-   Model attempts to pass another user's ID.
-   Model attempts to call an unregistered tool.
-   Model attempts arbitrary SQL.
-   Prompt injection inside CSV descriptions.
-   Malformed or excessive tool arguments.
-   Repeated tool-call loops.
-   Mutation request without user confirmation.

Expected outcome: server-side policy rejects the action regardless of
model wording.

------------------------------------------------------------------------

## 13. Performance and load testing

### 13.1 Workloads

Test separately: - Dashboard analytics reads. - Transaction
pagination. - CSV import of small, medium and maximum permitted files. -
Concurrent voice sessions. - Provider connection concurrency. -
Forecast/report jobs. - Slack event bursts.

### 13.2 Metrics

-   Request throughput.
-   p50/p95/p99 API latency.
-   Database query latency.
-   Connection-pool saturation.
-   Memory during CSV processing.
-   Import throughput and error rate.
-   Voice first-audio and total-turn latency.
-   Provider error and timeout rates.
-   Queue depth and job duration if workers are used.

### 13.3 Initial test profile

Use a modest, reproducible baseline rather than claiming
production-scale capacity:

-   20 synthetic users.
-   15K--20K transactions.
-   10 concurrent dashboard users.
-   3--5 concurrent voice sessions for initial smoke/load testing.
-   CSV files at several sizes up to the configured application limit.

Increase load only after measuring resource consumption and provider
limits. The Gnani account quota may be more restrictive than local
infrastructure.

------------------------------------------------------------------------

## 14. Reliability and failure-injection tests

Simulate: - PostgreSQL unavailable. - Redis unavailable. - Gnani STT
timeout. - Gnani TTS timeout. - Reasoning endpoint rate-limited. -
Provider returns malformed JSON/event. - Browser disconnects mid-turn. -
Worker crashes mid-import. - Database transaction fails. - Slack retries
event delivery. - Object storage returns an error.

Expected behavior: - No fabricated financial response. - No partial
transaction corruption. - Idempotent retry where supported. - Clear
user-visible failure state. - Correlation ID available for diagnosis. -
Sensitive information absent from logs.

------------------------------------------------------------------------

## 15. Test automation and CI

### 15.1 Backend commands

Suggested commands (adapt to actual project tooling):

``` bash
pytest -q
ruff check .
ruff format --check .
```

Run static typing if configured:

``` bash
mypy app
```

### 15.2 Frontend commands

``` bash
npm run lint
npm run test
npm run build
```

Run Playwright for critical browser journeys:

``` bash
npx playwright test
```

### 15.3 CI pipeline

On each pull request: 1. Install pinned dependencies. 2. Run backend
lint and type checks. 3. Run backend unit tests. 4. Start isolated
PostgreSQL and run migrations. 5. Run backend integration tests. 6. Run
frontend lint and unit tests. 7. Build frontend. 8. Run
security/dependency checks. 9. Build container image when configured.

Provider integration tests should be separate, opt-in jobs using
dedicated test credentials. Normal CI must not spend live speech
credits.

------------------------------------------------------------------------

## 16. Test case traceability

Maintain a test case registry with: - `test_id` - Feature/module -
Requirement or invariant - Preconditions - Input fixture - Expected
result - Test level - Automation status - Last run/build - Owner -
Severity if failed

Example IDs: - `FIN-MONEY-001` - `FIN-TRANSFER-004` - `CSV-MAP-003` -
`CSV-IDEMP-002` - `AUTH-ISOLATION-001` - `VOICE-SESSION-005` -
`VOICE-TOOL-002` - `ANOMALY-EVAL-001` - `FORECAST-LEAKAGE-001` -
`SLACK-REPLAY-001`

------------------------------------------------------------------------

## 17. Release and demo acceptance checklist

### Core data

-   [ ] User can upload at least one supported CSV format.
-   [ ] Preview reports valid and invalid rows.
-   [ ] User confirms import.
-   [ ] Imported transactions preserve source traceability.
-   [ ] Transfers/refunds are not incorrectly counted as ordinary
    expenses.

### Financial intelligence

-   [ ] Dashboard totals match hand-calculated fixtures.
-   [ ] Category and merchant breakdowns reconcile.
-   [ ] Period comparisons use correct calendar boundaries.
-   [ ] Budget utilization is correct.
-   [ ] Anomaly results include evidence and review state.
-   [ ] Forecast is labelled as an estimate and has a baseline
    comparison.

### Voice

-   [ ] Gnani STT smoke test succeeds.
-   [ ] Gnani TTS smoke test succeeds.
-   [ ] Voice session is authenticated.
-   [ ] One financial question selects the correct tool.
-   [ ] Spoken and dashboard answers match.
-   [ ] Cancellation/disconnect cleanup works.
-   [ ] Text fallback works if speech provider fails.

### Security

-   [ ] Cross-user access tests pass.
-   [ ] No secrets in frontend build.
-   [ ] No credentials in logs.
-   [ ] CSV upload limits and validation work.
-   [ ] LLM cannot execute arbitrary SQL or access another user.

### Reliability

-   [ ] Provider errors are handled.
-   [ ] Import retries are idempotent.
-   [ ] Demo data is seeded deterministically.
-   [ ] Health checks and useful logs are available.
-   [ ] Demo path works from a clean environment.

------------------------------------------------------------------------

## 18. Definition of done

A feature is done only when: - Its behavior is documented. - Inputs are
validated. - Authorization is tested. - Domain logic has unit tests. -
Persistence/API boundaries have integration tests. - Error and empty
states are handled. - Logs contain correlation metadata without
sensitive values. - Critical user journey is covered by E2E tests where
appropriate. - The feature passes CI.

**End of `test.md`.**
