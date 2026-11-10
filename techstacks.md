# FinSight --- Technology Stack

**Document:** `techstacks.md`\
**Status:** Proposed baseline --- implementation decisions must be
validated during setup\
**Product:** FinSight --- Voice-first Personal Financial Intelligence
Platform\
**Architecture style:** Modular monolith with a custom Python
voice-agent orchestration layer

------------------------------------------------------------------------

## 1. Purpose and decision principles

This document defines the proposed technologies for FinSight, why each
is used, where it belongs, and which choices remain conditional. It is
the technology reference for implementation; `architecture.md` defines
how these technologies interact, while `data_schema.md` defines the
persisted data model.

### 1.1 Product constraints

FinSight must support:

-   Personal financial CSV ingestion and normalization.
-   A voice-first multilingual conversational interface.
-   Deterministic financial analytics, budgeting, forecasting and
    anomaly detection.
-   A web dashboard and downloadable reports.
-   Slack as a secondary interaction channel.
-   Synthetic financial data for development and demonstrations.
-   Secure separation of each user's financial records.

### 1.2 Engineering principles

1.  **Backend owns financial truth.** All balances, totals, comparisons,
    forecasts and budget calculations are computed by application code
    and database queries---not invented by an LLM.
2.  **Gnani is an API provider, not our orchestration framework.**
    FinSight owns the Python voice-agent lifecycle, session state, tool
    registry, routing and error handling. Gnani provides speech
    capabilities through its APIs.
3.  **Provider adapters isolate external services.** STT, TTS and
    reasoning providers are accessed behind interfaces so providers can
    be replaced without rewriting the domain layer.
4.  **Start with a modular monolith.** Use one deployable FastAPI
    application with clear internal modules. Do not introduce
    microservices, Kafka or Kubernetes without measured need.
5.  **Use relational persistence for financial records.** PostgreSQL is
    the source of truth. Redis is optional infrastructure, not a second
    source of truth.
6.  **Money must be exact.** Use integer minor units or `Decimal`; never
    use binary floating-point for persisted monetary values.
7.  **Security is part of the design.** Secrets stay server-side; every
    financial query is scoped to the authenticated user; logs must not
    expose credentials or unnecessary transaction details.
8.  **Do not assume provider capabilities.** Verify the actual
    account-enabled Gnani models, request formats, streaming semantics,
    limits and inference endpoints before implementation.

------------------------------------------------------------------------

## 2. Proposed stack at a glance

  --------------------------------------------------------------------------
  Layer                   Proposed technology        Decision
  ----------------------- -------------------------- -----------------------
  Web frontend            React + TypeScript + Vite  Adopt

  UI styling              Tailwind CSS               Adopt

  Charts                  Recharts                   Adopt

  Frontend data fetching  TanStack Query             Adopt

  Frontend routing        React Router               Adopt

  Backend API             Python + FastAPI           Adopt

  Request/response        Pydantic                   Adopt
  validation                                         

  ORM and database access SQLAlchemy 2.x             Adopt

  Schema migrations       Alembic                    Adopt

  Primary database        PostgreSQL                 Adopt

  Cache / ephemeral       Redis                      Conditional; add when
  session state                                      required

  CSV processing          Python `csv` for simple    Adopt both selectively
                          streaming; Pandas for      
                          batch transformations      

  Numerical analysis      NumPy                      Adopt

  Classical ML            scikit-learn               Adopt selectively

  Time-series forecasting Statsmodels                Adopt for baseline
                                                     models

  Speech-to-text          Gnani Prisma API           Adopt, subject to
                                                     account/API validation

  Text-to-speech          Gnani Timbre API           Adopt, subject to
                                                     account/API validation

  Voice orchestration     Custom Python package      Adopt
                          within backend             

  Reasoning LLM           Evon 30B candidate or      Conditional
                          another verified endpoint  

  Background jobs         FastAPI background tasks   Decide after workload
                          only for lightweight work; spike
                          queue worker for durable   
                          jobs                       

  Slack integration       Slack Web API / Events API Adopt for MVP
                                                     integration

  Testing                 pytest, HTTPX, factory     Adopt
                          fixtures                   

  Frontend testing        Vitest + React Testing     Adopt
                          Library; Playwright for    
                          E2E                        

  Local environment       Docker Compose             Adopt

  CI                      GitHub Actions             Adopt

  Observability           Python structured logging; Adopt incrementally
                          OpenTelemetry-compatible   
                          instrumentation            
  --------------------------------------------------------------------------

Version policy: use currently supported stable releases at
implementation time, pin exact versions in lockfiles, and record the
tested Python and Node versions. Do not copy unverified version numbers
from this proposal.

------------------------------------------------------------------------

## 3. Frontend

### 3.1 React + TypeScript + Vite

**Purpose:** Build the FinSight single-page web application.

Responsibilities:

-   Authentication and application navigation.
-   CSV upload and import progress.
-   Dashboard KPI cards and charts.
-   Transaction history and filtering.
-   Budget and savings-goal management.
-   Voice interaction controls and audio playback.
-   Reports and downloadable exports.
-   User-facing anomaly review and correction flows.

**Why this choice:**

-   React supports a component-oriented dashboard and interactive voice
    experience.
-   TypeScript catches contract mismatches between frontend and backend.
-   Vite provides a lightweight development and build workflow.
-   The frontend can use REST for ordinary operations and WebSockets for
    live voice sessions.

The frontend must not contain Gnani API secrets, database credentials,
privileged model credentials or financial business rules.

### 3.2 Tailwind CSS

Use Tailwind for consistent styling and responsive layouts. Define a
small design-token layer for colors, spacing, typography, radii and
component states. Avoid mixing multiple styling systems without a
concrete requirement.

### 3.3 Recharts

Use Recharts for:

-   Monthly income and expense trends.
-   Category-wise spending breakdown.
-   Merchant comparisons.
-   Budget utilization.
-   Cash-flow forecast with uncertainty bands where supported.

Charts must display the time period, currency and aggregation basis. A
chart must not silently mix currencies or treat transfers as expenses.

### 3.4 TanStack Query and React Router

-   **TanStack Query:** server-state fetching, caching, loading/error
    states and invalidation after mutations.
-   **React Router:** page and nested-route navigation.

Do not use browser storage as the authoritative location for financial
data. Client caches are transient and must be cleared or partitioned
appropriately on logout/account changes.

### 3.5 Browser voice capture

Use browser microphone APIs through a dedicated voice feature module.
Capture and encode audio in the format required by the selected
backend/Gnani streaming path. The exact codec, sample rate, frame size
and browser compatibility must be validated in the voice integration
spike.

The browser communicates with FinSight's backend---not directly with
Gnani. This keeps provider credentials private and gives the backend
control over authentication, sessions and cancellation.

------------------------------------------------------------------------

## 4. Backend and application framework

### 4.1 Python + FastAPI

**Purpose:** Main application backend and API boundary.

Responsibilities:

-   Authentication and authorization.
-   CSV upload and ingestion orchestration.
-   Financial domain services.
-   Voice WebSocket session management.
-   Gnani provider adapters.
-   LLM orchestration and controlled tool calling.
-   Slack integration endpoints.
-   Report generation.
-   Background-job submission and status APIs.

FastAPI is selected for typed request handling, async I/O, WebSocket
support and straightforward integration with Python's data/ML ecosystem.

### 4.2 Pydantic

Use Pydantic models for:

-   API request and response contracts.
-   CSV mapping configuration.
-   Normalized transaction validation.
-   Voice-agent tool input/output schemas.
-   LLM structured-output validation.
-   Application settings.

Pydantic validation is not a substitute for database constraints or
authorization checks. Validate at each trust boundary.

### 4.3 SQLAlchemy 2.x and Alembic

-   **SQLAlchemy:** relational queries, repositories, transactions and
    ORM mappings.
-   **Alembic:** version-controlled database migrations.

Use explicit transaction boundaries for imports and financial mutations.
Avoid embedding complex business rules inside ORM model hooks. Keep
domain calculations in service modules and query-heavy aggregations in
repositories or dedicated query services.

### 4.4 API style

Use REST for normal application operations and WebSockets for
interactive voice sessions.

Suggested route groups:

-   `/api/v1/auth`
-   `/api/v1/accounts`
-   `/api/v1/imports`
-   `/api/v1/transactions`
-   `/api/v1/analytics`
-   `/api/v1/budgets`
-   `/api/v1/goals`
-   `/api/v1/recurring`
-   `/api/v1/anomalies`
-   `/api/v1/forecasts`
-   `/api/v1/reports`
-   `/api/v1/voice`
-   `/api/v1/integrations/slack`

Keep API versioning from the beginning. Use consistent error envelopes
and request correlation IDs.

------------------------------------------------------------------------

## 5. Database and persistence

### 5.1 PostgreSQL --- primary source of truth

PostgreSQL stores:

-   Users and authentication-related records.
-   Bank accounts and account metadata.
-   Imported statement files and import jobs.
-   Canonical financial transactions.
-   Merchant and category mappings.
-   Budgets and savings goals.
-   Recurring-payment observations.
-   Anomaly results and user review decisions.
-   Forecast runs and forecast outputs.
-   Voice conversation metadata where retention is required.
-   Notification preferences and delivery records.
-   Slack workspace/user linkage, where applicable.

**Why PostgreSQL:**

-   Strong relational integrity for financial entities.
-   Transactions and constraints for reliable ingestion.
-   Numeric/decimal types for exact monetary values.
-   Indexing and aggregation for analytical queries.
-   JSONB for limited flexible metadata without abandoning relational
    structure.

### 5.2 Monetary representation

Choose one consistent representation per currency:

-   Preferred: store `amount_minor` as a signed `BIGINT` (for INR,
    paise; for USD, cents), alongside an ISO currency code.
-   For calculations requiring fractional intermediate values, use
    Python `Decimal` and explicit rounding rules.
-   Never use Python `float` or PostgreSQL `REAL`/`DOUBLE PRECISION` for
    monetary values.

Do not assume every currency has two decimal places. Currency exponent
must be derived from a currency metadata table/library or an explicit
supported-currency policy.

### 5.3 Redis --- conditional

Redis may be introduced for:

-   Short-lived voice session coordination.
-   WebSocket session metadata shared across workers.
-   Rate-limit counters.
-   Short-lived cached analytics results.
-   Job broker/backend if the selected queue requires it.

Redis must not become the authoritative store for transactions, budgets
or goals. If Redis is unavailable, the system should fail safely; it
must not return stale financial values as if they were current.

### 5.4 File/object storage

Raw uploaded statements and generated reports may require durable object
storage in deployed environments. For local development, use a
non-public local data directory or an S3-compatible object store. Store
only a storage key and metadata in PostgreSQL; do not store public file
URLs for sensitive statements.

Define retention and deletion behavior for raw uploads. Never expose
uploaded statements through a public static directory.

------------------------------------------------------------------------

## 6. Gnani speech integration

### 6.1 Gnani Prisma --- speech-to-text

**Role:** Convert user speech into text for the conversation
orchestrator.

The studied documentation describes Prisma v3 and these broad
capabilities:

-   Multilingual transcription and code-mixed speech support.
-   Language identification modes.
-   Verbatim, transcription, code-mix and transliteration modes.
-   Keyterm prompting.
-   REST and WebSocket streaming interfaces.

Previously reviewed documentation listed:

-   REST: `POST https://api.vachana.ai/stt/v3`
-   Streaming WebSocket: `wss://api.vachana.ai/stt/v3/stream`
-   REST authentication header: `X-API-Key-ID`

These details must be checked against the current official documentation
and the credentials issued for the hackathon before coding. Do not
assume a Speech API key uses the same header or permissions as any other
Gnani product.

**Adapter responsibility:** `GnaniPrismaSTT` should own
provider-specific authentication, connection setup, audio framing, event
parsing, timeouts, error translation and cleanup. The voice orchestrator
should consume provider-neutral transcript events.

### 6.2 Gnani Timbre --- text-to-speech

**Role:** Convert the assistant's final response into spoken audio.

The studied documentation describes REST, SSE and WebSocket options,
multiple audio formats and configurable voice/language parameters.
Previously reviewed endpoint references included:

-   REST: `POST https://api.vachana.ai/api/v1/tts/inference`
-   SSE: `POST https://api.vachana.ai/api/v1/tts/sse`
-   WebSocket: `wss://api.vachana.ai/api/v1/tts`

These are reference details, not permission to hard-code assumptions.
Confirm current request/response formats, model identifiers, supported
languages, audio encoding and streaming behavior from the current Gnani
documentation.

**Adapter responsibility:** `GnaniTimbreTTS` should accept normalized
text and voice settings and return audio chunks or a completed audio
result through a provider-neutral interface.

### 6.3 Credential handling

-   Keep Gnani credentials in backend environment variables or a secret
    manager.
-   Never expose them in React/Vite environment variables prefixed for
    browser exposure.
-   Never log authorization headers or raw API keys.
-   Separate development and production credentials.
-   Use the minimum permissions required.
-   Rotate a key immediately if exposed.

Suggested environment names (names only; never commit values):

``` dotenv
GNANI_STT_API_KEY_ID=
GNANI_TTS_API_KEY_ID=
GNANI_STT_BASE_URL=
GNANI_TTS_BASE_URL=
```

The actual credential names and header format must match the issued
Gnani key and current docs. Do not assume one key is valid for both
services until tested.

### 6.4 Voice provider abstraction

Define interfaces similar to:

``` python
class SpeechToTextProvider(Protocol):
    async def transcribe(self, audio, options) -> Transcript:
        ...

    async def stream(self, audio_frames, options) -> AsyncIterator[TranscriptEvent]:
        ...


class TextToSpeechProvider(Protocol):
    async def synthesize(self, text, options) -> AudioResult:
        ...

    async def stream(self, text, options) -> AsyncIterator[AudioChunk]:
        ...
```

These are conceptual contracts; implementation must reflect the exact
provider behavior. Do not promise partial transcript events or
incremental text-to-audio generation unless the selected endpoint
explicitly supports them.

------------------------------------------------------------------------

## 7. Voice-agent reasoning and orchestration

### 7.1 Custom Python voice-agent package

FinSight will implement its own orchestration layer. It is responsible
for:

-   Session lifecycle and authenticated user context.
-   Conversation state and bounded history.
-   Language and intent handling.
-   Tool selection and schema validation.
-   Calling deterministic financial services.
-   Handling tool errors and clarification.
-   Response generation and speech handoff.
-   Cancellation, timeout and cleanup.
-   Audit/correlation metadata.

Suggested internal modules:

``` text
voice_agent/
  agent.py
  session_manager.py
  conversation.py
  context_manager.py
  intent_router.py
  tool_registry.py
  tool_executor.py
  response_generator.py
  prompts/
  schemas/
```

Do not begin with multiple autonomous agents. A single orchestrator with
a controlled registry of financial tools is easier to test, secure and
demonstrate. Specialized agents can be considered later if distinct
workflows justify them.

### 7.2 Reasoning model --- Evon 30B is conditional

Evon 30B is a candidate because its model card describes multilingual
reasoning and tool-calling capabilities. However:

-   The model card does not prove that a hosted inference endpoint is
    included with the hackathon account.
-   A self-hosted deployment may require substantial GPU infrastructure.
-   Tool-calling compatibility, context limits, latency, rate limits and
    pricing must be verified.
-   Financial-domain outputs must be evaluated before use.

**Do not hard-code Evon as a confirmed hosted service.** Implement a
`ReasoningProvider` interface and select a model only after verifying
endpoint access and running a tool-calling proof of concept.

If no suitable Evon endpoint is supplied, use another permitted,
accessible model endpoint while preserving the same interface.

### 7.3 Controlled tool calling

Expose narrowly scoped tools such as:

-   `get_spending_summary`
-   `get_category_breakdown`
-   `compare_periods`
-   `get_top_merchants`
-   `get_payment_mode_summary`
-   `get_recurring_payments`
-   `get_savings_ratio`
-   `get_budget_status`
-   `get_forecast`
-   `find_unusual_transactions`
-   `simulate_savings_goal`

Every tool must:

1.  Validate its input schema.
2.  derive the user identity from authenticated server-side context, not
    an LLM-supplied user ID.
3.  enforce date-range and result-size limits.
4.  call the financial domain layer.
5.  return structured, traceable results.
6.  avoid arbitrary SQL execution.

The LLM may explain verified results; it must not invent amounts,
transaction records or forecast certainty.

------------------------------------------------------------------------

## 8. Analytics, forecasting and ML

### 8.1 Pandas and NumPy

Use Pandas for batch CSV normalization and analysis where its memory
cost is acceptable. Use Python's built-in `csv` module or chunked
processing for large files. Use NumPy for numerical operations that do
not involve exact currency arithmetic.

Interactive dashboard totals should generally be computed using indexed
SQL aggregations rather than loading a user's entire transaction history
into Pandas for every request.

### 8.2 scikit-learn

Use scikit-learn for optional anomaly models such as Isolation Forest
after a deterministic baseline exists and sufficient historical data is
available.

An ML anomaly score is an investigation signal, not a fraud verdict.
Store model version, features/score metadata and review outcome where
useful.

### 8.3 Statsmodels

Use Statsmodels for transparent baseline time-series models, such as
moving-average/exponential-smoothing or suitable ARIMA-family
approaches, depending on data sufficiency and evaluation results.

Forecasting must:

-   Respect chronological train/validation/test splits.
-   Avoid future-data leakage.
-   Include a baseline comparator.
-   Report uncertainty where the method supports it.
-   Abstain or show insufficient-history messaging when data is
    inadequate.

Do not promise reliable personalized forecasts from a few transactions
or a short history.

------------------------------------------------------------------------

## 9. Slack integration

Use Slack's official Web API and Events API for the secondary interface.

Responsibilities:

-   Receive authorized Slack events.
-   Verify Slack request signatures.
-   Map a Slack user/workspace to an authenticated FinSight user.
-   Route supported questions through the same financial tool layer.
-   Return concise text summaries and links to the FinSight dashboard
    where appropriate.

Slack must not contain a separate financial calculation implementation.
Both voice and Slack should invoke the same domain services.

Store signing secrets and bot tokens only on the backend. Apply
idempotency to event handling because Slack event delivery can be
retried.

------------------------------------------------------------------------

## 10. Background processing and job execution

Potential asynchronous workloads:

-   CSV parsing, normalization and enrichment.
-   Large import validation and commit.
-   Forecast generation.
-   Periodic anomaly evaluation.
-   Recurring-payment detection.
-   Report generation.
-   Scheduled notifications and summaries.

For the first vertical slice, lightweight tasks can run synchronously or
through FastAPI background tasks only if losing the task on process
restart is acceptable.

For durable, retryable jobs, introduce a worker and queue after choosing
an operationally suitable option. Candidate: Celery with Redis or
another supported broker/backend. Do not add a queue merely for
architectural appearance.

A job must have a durable status record, idempotency key, bounded retry
policy and observable failure state.

------------------------------------------------------------------------

## 11. Testing and developer tooling

### Backend

-   `pytest` for unit and integration tests.
-   `httpx` for FastAPI endpoint tests.
-   Database fixtures using an isolated test database.
-   Property-based tests may be added for money, date and import
    invariants.

### Frontend

-   Vitest for unit/component tests.
-   React Testing Library for user-facing behavior.
-   Playwright for browser-level critical journeys.

### Code quality

-   Ruff for Python linting and formatting.
-   mypy or Pyright for static typing where valuable.
-   ESLint and Prettier for TypeScript/React.
-   pre-commit hooks for repeatable local checks.

### CI

GitHub Actions should run:

1.  Dependency and lockfile checks.
2.  Backend lint/type checks.
3.  Backend unit and integration tests.
4.  Frontend lint and tests.
5.  Production frontend build.
6.  Optional container build and security scan.

Use deterministic fixtures and mock external Gnani/LLM calls in ordinary
CI. Run a separate opt-in provider integration suite using secrets
stored in CI.

------------------------------------------------------------------------

## 12. Local development and deployment

### 12.1 Docker Compose

Use Docker Compose for local PostgreSQL and optional Redis, plus the
application services where helpful. Keep hot-reload development
convenient.

Initial local services:

-   `frontend`
-   `backend`
-   `postgres`
-   optional `redis`
-   optional `worker`

Do not add Kubernetes for the hackathon MVP.

### 12.2 Environment configuration

Use a typed settings module backed by environment variables. Maintain:

-   `.env.example` with placeholders only.
-   `.env` excluded from Git.
-   Separate development/test/production settings.
-   Startup validation for required configuration.
-   No secrets in source control, frontend bundles, test fixtures or
    logs.

### 12.3 Deployment shape

The initial deployment can use:

-   One frontend static deployment.
-   One FastAPI backend deployment supporting HTTP and WebSockets.
-   Managed PostgreSQL or a secured PostgreSQL instance.
-   Optional Redis if shared session state or rate limiting requires it.
-   A separate worker only when durable background processing is
    introduced.

The deployment platform is intentionally not fixed in this document.
Select it based on hackathon constraints, WebSocket support,
environment-variable/secret management, database connectivity and cost.

------------------------------------------------------------------------

## 13. Proposed repository layout

``` text
finsight/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── dashboard/
│   │   │   ├── transactions/
│   │   │   ├── budgets/
│   │   │   ├── goals/
│   │   │   ├── reports/
│   │   │   └── voice/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── services/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── websocket/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   ├── analytics/
│   │   │   ├── forecasting/
│   │   │   ├── anomalies/
│   │   │   ├── budgeting/
│   │   │   └── reporting/
│   │   ├── voice_agent/
│   │   ├── providers/
│   │   │   ├── gnani/
│   │   │   └── reasoning/
│   │   ├── integrations/
│   │   │   └── slack/
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   └── pyproject.toml
│
├── data/
│   ├── synthetic/
│   └── samples/
├── docs/
│   ├── techstacks.md
│   ├── architecture.md
│   ├── data_schema.md
│   ├── test.md
│   └── system_design.md
├── scripts/
├── docker-compose.yml
├── .env.example
└── README.md
```

This is a proposed organization, not a requirement to create every
directory immediately. Keep modules small and add files when
implementation needs them.

------------------------------------------------------------------------

## 14. Decisions still requiring validation

  -----------------------------------------------------------------------
  Decision                Current status          Required validation
  ----------------------- ----------------------- -----------------------
  Gnani Prisma account    Expected / to verify    Create a minimal STT
  access                                          request with issued
                                                  credentials

  Gnani Timbre account    Expected / to verify    Create a minimal TTS
  access                                          request with issued
                                                  credentials

  Exact Gnani auth header Pending                 Follow current
  per API                                         endpoint-specific
                                                  documentation

  Streaming STT event     Pending implementation  Verify framing,
  semantics               test                    transcript events,
                                                  disconnect behavior

  Streaming TTS semantics Pending implementation  Verify chunk delivery
                          test                    and cancellation
                                                  behavior

  Evon hosted inference   Unconfirmed             Obtain endpoint, auth,
  access                                          model ID, limits and
                                                  pricing

  Browser audio format    Pending                 Validate target
                                                  browsers and provider
                                                  requirements

  Redis                   Conditional             Add only for shared
                                                  ephemeral state/rate
                                                  limits/queue

  Durable task queue      Conditional             Decide after
                                                  import/forecast
                                                  workload spike

  Deployment provider     Pending                 Evaluate WebSocket
                                                  support, cost and
                                                  hackathon constraints

  Slack app permissions   Pending                 Define minimum scopes
                                                  and install/test
                                                  workspace app
  -----------------------------------------------------------------------

### 14.1 Explicitly excluded from the initial MVP

Unless a measured requirement emerges, do not introduce:

-   Gnani Agent Builder.
-   Microservices.
-   Kafka or event-streaming infrastructure.
-   Kubernetes.
-   A vector database solely to answer questions about structured
    transactions.
-   An LLM-generated Text-to-SQL path for personal financial records.
-   Multiple autonomous agents for simple tool routing.
-   A second database as the financial source of truth.

------------------------------------------------------------------------

## 15. Implementation order

1.  Create the React/TypeScript and FastAPI project foundations.
2.  Establish PostgreSQL, SQLAlchemy and Alembic migrations.
3.  Implement authentication and user-scoped repository access.
4.  Implement CSV ingestion and canonical transaction normalization.
5.  Implement deterministic analytics tools and verify monetary
    correctness.
6.  Build the voice-agent provider interfaces and session manager.
7.  Integrate Gnani Prisma and Timbre with minimal provider smoke tests.
8.  Integrate a verified reasoning endpoint and constrained tool
    calling.
9.  Connect voice UI to the backend WebSocket.
10. Add budgeting, goals, anomalies and forecasting.
11. Add Slack through the shared financial tool layer.
12. Add durable background processing, caching and operational hardening
    only where needed.

------------------------------------------------------------------------

## 16. Definition of a successful stack setup

The stack is considered established when:

-   Frontend and backend run locally from documented commands.
-   Database migrations can create a clean schema.
-   A user can upload a supported CSV and inspect normalized
    transactions.
-   Financial totals are exact and covered by tests.
-   The backend can make authenticated Gnani STT and TTS calls.
-   A voice session can invoke at least one authenticated financial
    tool.
-   No provider secret is exposed to the browser or logs.
-   A second user cannot access the first user's data.
-   CI runs the core test and build pipeline successfully.

**End of `techstacks.md`.**
