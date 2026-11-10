# FinSight --- Production-Grade Agent Reliability Methods

## 1. Purpose and principles

This document defines methods for making FinSight's LLM pipeline
reliable, observable, secure and continuously evaluated. It describes an
engineering target, not a claim that these capabilities already exist.

Principles: 1. The model interprets; deterministic services establish
financial truth. 2. Prompts guide behaviour; backend code enforces
policy. 3. Every tool call is typed, authorized, bounded and observable.
4. Material financial claims must be grounded in verified application
data. 5. Writes require authorization, confirmation and idempotency. 6.
Evals cover the full execution trace, not just final wording. 7.
Failures must be visible, recoverable and safe. 8. Zero hallucinations
cannot be guaranteed for arbitrary inputs; the system must prevent
unsupported model output from becoming financial truth or unauthorized
action.

## 2. Reference architecture

`User input → Normalization → Session/context → Intent and plan → Harness checks → Tool selection → Schema validation → Authorization → Deterministic execution → Result/evidence validation → Response synthesis → Output validation → Voice/UI`

Reactive path:

`Domain event → Durable event record → Worker/rule evaluation → Alert persistence → User-scoped delivery → Acknowledgement/action`

Quality path:

`Versioned code/prompts/models/tools → Offline Evals → Regression gates → Staging → Controlled release → Production telemetry → Failure review → New eval cases`

  ---------------------------------------------------------------------------
  Component               Responsibility              Must not do
  ----------------------- --------------------------- -----------------------
  LLM                     Understand language,        Invent balances,
                          propose plans, select       authorize access or
                          tools, explain verified     calculate authoritative
                          results                     totals

  Harness                 State, validation, limits,  Trust arbitrary model
                          orchestration               instructions

  Tool registry           Typed supported             Offer unrestricted SQL
                          capabilities                

  Financial services      Deterministic business      Depend on LLM
                          logic                       arithmetic

  Database                Persistence and constraints Trust model-supplied
                                                      user identity

  Verification            Validate                    Treat model self-check
                          facts/evidence/invariants   as proof

  Evals                   Measure behaviour and       Treat one score as
                          regression                  proof of safety

  Observability           Actual events and metrics   Log secrets or hidden
                                                      chain-of-thought
  ---------------------------------------------------------------------------

## 3. Hallucination containment and grounding

For user-specific financial questions: - Retrieve facts through
authorized tools. - Calculate values in deterministic backend code. -
Pass structured results and provenance to response synthesis. - Validate
material claims against returned facts. - If evidence is missing, stale,
contradictory or insufficient, state the limitation.

Example internal fact contract (illustrative values only):

``` json
{
  "metric": "category_spending",
  "category": "Food & Dining",
  "period_start": "2026-10-01",
  "period_end_exclusive": "2026-11-01",
  "amount_minor": 130000,
  "currency": "INR",
  "transaction_count": 4,
  "evidence_ids": ["TXN_001", "TXN_002"],
  "calculation_version": "category_spending_v1"
}
```

Validate that evidence exists, belongs to the authenticated user,
matches the period and supports the aggregation. Prefer structured fact
validation over unreliable free-form claim extraction for every
sentence.

The agent should clarify missing parameters, distinguish zero results
from failed retrieval, separate actuals from projections and refuse
unsupported external actions.

Treat user messages, CSV descriptions, merchant names and retrieved free
text as untrusted data---not instructions. Tool allowlists, permissions
and data boundaries belong in application code.

## 4. Agent harness engineering

### Explicit execution states

Use a typed state machine, for example:
`RECEIVED → NORMALIZING → UNDERSTANDING → PLANNING → TOOL_EXECUTING → VERIFYING → RESPONDING → COMPLETED`

Also support `NEEDS_CLARIFICATION`, `WAITING_FOR_CONFIRMATION`, `FAILED`
and `CANCELLED`. Define allowed transitions and terminal states.

### Bounded execution

Configure maximum orchestration duration, model calls, tool calls, tool
rounds, per-tool timeout, response size, context/token budget and retry
count. Stop safely when limits are reached.

### Structured outputs

Use Pydantic or equivalent for intent, plans, tool arguments,
clarification requests, action proposals and response facts. Reject
malformed or out-of-range values.

### Tool registry

Each tool needs a stable name/version, precise description, typed
input/output, permission, read/write classification, confirmation
requirement, timeout/retry policy, idempotency policy, evidence
behaviour and error contract. Prefer focused tools; avoid catch-all SQL
tools and needless agents.

### Identity and authorization

Derive user identity from authenticated application context, never from
model-generated arguments. Scope every query and referenced record. Test
cross-user access. Consider database row-level security as defence in
depth.

### Retries and cancellation

Retry only transient and retry-safe operations. Use backoff with jitter
where appropriate. Never blindly retry non-idempotent writes. Propagate
cancellation where supported and make partial failures explicit.

### Conversation state

Persist compact structured state: session/user references, current
intent, reporting period, category/merchant filters, last relevant
result reference, pending action status and language. Expire state
deliberately. Old assistant statements are not current financial truth;
re-fetch current values.

## 5. Intent routing and planning

Maintain a versioned taxonomy matching implemented capabilities, such
as: - `financial_summary` - `category_spending` - `merchant_spending` -
`period_comparison` - `transaction_search` - `transaction_evidence` -
`upi_analysis` - `budget_status` - `budget_create_or_update` -
`goal_create_or_update` - `recurring_payment_analysis` -
`anomaly_investigation` - `forecast` - `what_if_simulation` -
`alert_management` - `unsupported_or_out_of_scope`

For multi-part requests, the model may propose a structured plan; the
harness validates tools, dependencies and limits. Example: compare
expenses, identify category drivers, retrieve evidence, fetch dining
baseline and run a deterministic 20% savings simulation.

Measure intent accuracy, tool selection, argument exact match,
clarification correctness, plan validity, unnecessary tool calls and
unsupported tool calls.

## 6. Prompt engineering and management

Use versioned prompt components: 1. Core system policy. 2.
Financial-domain rules. 3. Intent/planning instructions. 4. Tool
descriptions. 5. Response synthesis. 6. Voice/language instructions. 7.
Write-action confirmation policy.

Prompts specify supported capabilities, tool usage, required parameters,
clarification/abstention, authoritative sources, error handling,
actual-versus-forecast distinction and confirmation requirements.

Tool descriptions are part of the routing interface; keep them precise
and non-overlapping.

Track prompt ID/version, model/provider/version, tool schema version and
orchestration version. Run regression Evals after every material prompt
change.

### Prompt caching

Caching is an optimization, not a reliability mechanism. Where
supported, put stable instructions/tool definitions in reusable prefixes
and dynamic user context later. Follow provider-specific eligibility
rules. Measure cache hits, cached tokens, latency and cost. Never cache
current financial facts as authoritative truth. Do not claim caching
without runtime evidence.

## 7. Financial correctness

Use Decimal or integer minor units for money. Define canonical rules
for: - Income/expense signs. - Internal transfers. - Refunds and
reversals. - Duplicate imports. - Pending/settled status if
represented. - Currency and FX if supported. - Time zones and period
boundaries. - Account balance versus transaction-derived cash flow.

Reconciliation invariants: - Category totals reconcile to eligible
transactions. - Merchant totals reconcile to filtered transactions. -
Refund and transfer treatment is consistent. - Imports are idempotent. -
Dashboard, voice and reports share the same financial definitions.

Forecasts require chronological splits, baseline comparisons, suitable
error metrics, leakage prevention, data coverage, horizon metadata and
uncertainty where supported. Insufficient history must be explicit.

## 8. Action safety

All writes are enforced by application code.

**Prepare:** interpret, validate, authorize, read current state, create
exact proposal and return confirmation summary.

**Confirm/execute:** verify authenticated ownership, action
ID/status/expiry, revalidate permissions and current state, execute
transactionally, enforce idempotency, persist audit record and return
the actual updated resource.

Support cancellation and expiry. A database write is not an external
bank action. Do not claim autopay changes, transfers, card freezes or
disputes without a genuine authorized integration.

## 9. Reactive/event-driven behaviour

A reactive agent responds to actual events or scheduled
evaluations---not a monitoring animation.

1.  Record a domain event.
2.  Process it asynchronously.
3.  Evaluate deterministic rules.
4.  Persist an alert with source references.
5.  Deliver to the correct user/session.
6.  Allow inspection and acknowledgement.

Require idempotency, retries/failure handling, duplicate suppression,
user-scoped delivery, persistent history and worker/queue monitoring.
Start with the simplest durable worker architecture that fits the
deployment; do not add Kafka without evidence.

## 10. LLM evaluation framework

Evals are repeatable measurements of model, prompt, harness, tool and
integration behaviour.

### Dataset schema

Each versioned case should include case ID, fixture user/session,
query/language, expected intent, expected tool(s), expected arguments,
clarification/abstention expectation, expected result/reference facts,
required evidence, expected action state and safety expectations.

Use synthetic or anonymized fixtures.

### Initial coverage

An initial target of 300--500 carefully designed cases is reasonable: -
Intent classification. - Tool selection and arguments. - Numerical
correctness. - Multi-turn context. - Hindi/Hinglish. - Multi-tool
planning. - Write confirmation/authorization. - Unsupported/adversarial
requests. - Reactive event processing. - Failure recovery.

### Evaluation layers

**A. Deterministic** - Schema validity. - Intent labels and tool
names/arguments. - Database results and monetary calculations. -
Evidence existence/ownership. - Confirmation state and event
idempotency.

**B. Integration** - Real orchestrator with test database. - Tool
execution and results. - Session/follow-up behaviour. - WebSocket
delivery. - Provider adapters using mocks plus opt-in live smoke tests.

**C. Model/LLM** - Relevance, clarity, completeness, grounded
explanation and appropriate abstention.

**D. Adversarial** - Prompt injection in user/imported data. - Malformed
tool calls. - Missing/contradictory data. - Cross-user references. -
Provider timeouts. - Duplicate events/retries. - Unusual
phrasing/languages.

### Metrics

  Metric                    Meaning
  ------------------------- ----------------------------------------
  Intent accuracy           Correct intent / eligible cases
  Tool selection accuracy   Correct tool / cases requiring tools
  Argument exact match      Correct required parameters
  Tool success rate         Successful valid executions
  Numerical correctness     Result matches deterministic reference
  Evidence validity         Evidence exists and is authorized
  Grounded claim rate       Factual claims supported by evidence
  Unsupported-claim rate    Unsupported factual claims
  Confirmation compliance   Protected writes correctly gated
  Multi-turn success        Follow-ups preserve intended context
  P50/P95 latency           End-to-end and per-stage latency
  Cost/request              Model and infrastructure cost

Define denominators, sample counts and confidence intervals where
useful. Do not hide failed or skipped cases.

### LLM-as-a-Judge

Use a separate evaluator model for qualitative relevance, clarity and
completeness. Supply query, reference facts, actual response, trace and
a fixed rubric. Calibrate against human-reviewed samples and track
judge/rubric versions.

Never rely on an LLM judge as the authority for arithmetic, ownership,
authorization, write success or evidence existence.

### Dataset splits

Maintain development, validation and held-out test sets. Do not
repeatedly tune against the held-out set. Version datasets and fixtures.

### Regression gates

Run Evals when prompts, tool schemas, routing, models, financial
services or state handling change. Critical safety tests are hard gates;
do not average them away with high general scores.

## 11. Observability and tracing

Every request should have a correlation/trace ID linking frontend, voice
session, STT, model calls, tools, database operations, evidence
validation and TTS.

Emit actual backend events for: - Request received. - Intent resolved. -
Clarification required. - Plan validated. - Tool
selected/started/completed/failed. - Database result count. - Evidence
validation. - Action awaiting confirmation/executed/cancelled. -
Response and TTS lifecycle. - Request completed/failed.

Monitor tool failures, SQL errors, STT/TTS latency, end-to-end
P50/P95/P99, tokens/cache usage, cost, queue lag and alert delivery
failures.

Redact sensitive data, restrict trace access, define retention and never
log secrets or hidden chain-of-thought. The UI must render actual
lifecycle events, never fabricated progress.

## 12. Continuous release process

**Development:** unit tests, tool/auth tests, prompt versioning and fast
deterministic Evals.

**CI:** unit/integration tests, core agent regression cases and hard
safety gates; publish evaluation reports.

**Staging:** synthetic data, end-to-end conversations, provider smoke
tests, WebSocket/reactive tests and failure recovery.

**Production:** controlled releases, latency/error/cost monitoring,
privacy-safe quality review and conversion of verified failures into
regression cases.

Do not automatically change prompts or train from raw user feedback.
Review and validate improvements before release.

## 13. Suggested stack

  Need                Initial choice
  ------------------- ------------------------------------------------
  Orchestration       Existing custom Python orchestrator
  Schemas             Pydantic
  Database            SQLAlchemy + PostgreSQL
  Tests               Pytest
  Evals               Custom Python runner + versioned JSON/JSONL
  Qualitative judge   Separate evaluator model, calibrated by humans
  Tracing             OpenTelemetry
  Error monitoring    Sentry or equivalent
  CI                  Existing GitHub Actions/CI
  Prompts             Version-controlled templates
  Background work     Existing worker or lightweight durable queue

Optional: LangSmith for traces/datasets/experiments; DeepEval for
evaluation workflows; Ragas if a genuine retrieval feature is later
added; Prometheus/Grafana when operational scale warrants it.

Do not introduce RAG for structured transaction analytics. PostgreSQL
tools and deterministic services remain the primary data path.

## 14. Implementation phases

1.  **Baseline:** map request path, prompts, tools, schemas; build
    fixtures; record baseline failures.
2.  **Harness:** typed registry, state machine, bounded calls, auth,
    validation, confirmation and idempotency.
3.  **Grounding:** standard financial result contracts, evidence,
    deterministic calculations and abstention.
4.  **Prompts:** hierarchy, versioning, routing and clarification;
    caching only where supported.
5.  **Evals/observability:** automated runner, metrics, traces and CI
    gates.
6.  **Reactive reliability:** durable events, idempotent workers,
    persistent alerts and user-scoped delivery.

Implement incrementally. Test and inspect real integration after each
phase.

## 15. Production-readiness criteria

Do not declare production readiness merely because a voice interface,
tool registry or demo exists.

Verify: - Supported intents have tested routing. - Tools have typed
schemas and authorization. - Financial values are deterministic and
reconciled. - Evidence is real and user-scoped. - Unsupported requests
are handled honestly. - Writes require confirmation and are
idempotent. - Alerts originate from actual events. - Traces represent
actual backend activity. - Critical safety tests pass. - Evals are
reproducible and versioned. - Latency, errors, tokens and cost are
measured. - Sensitive data is protected. - Provider outages and partial
failures have safe behaviour. - Retention, recovery and operational
ownership are defined.

Production readiness is a risk-based release decision supported by
evidence---not a label generated by the LLM.

## 16. Final principle

The target is not an agent that never makes a mistake. The target is a
system in which the model has bounded authority, the application owns
truth and permissions, important actions are validated, financial claims
are grounded, failures are observable, Evals catch regressions and users
can understand what the system did and why.
