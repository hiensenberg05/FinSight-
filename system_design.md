# FinSight --- Production System Design

**Document:** `system_design.md`\
**Status:** Production-oriented reference design; implementation must be
driven by measured requirements\
**Architecture baseline:** Modular monolith with independently scalable
workers and provider adapters\
**Primary store:** PostgreSQL\
**Primary interface:** REST + WebSocket voice gateway\
**Voice providers:** Gnani Prisma STT and Timbre TTS through backend
adapters

------------------------------------------------------------------------

## 1. Purpose

This document describes the operational and scalability mechanisms
required to evolve FinSight from a hackathon MVP into a reliable
production service.

It expands the architecture document with: - Capacity planning and
scaling strategy. - API and provider rate limiting. - Caching and cache
invalidation. - Database connection management and query performance. -
Asynchronous jobs and event delivery. - Voice-session concurrency and
backpressure. - Idempotency, retries and circuit breakers. - Security
controls and abuse prevention. - Observability, SLOs, incident response
and disaster recovery. - Deployment, rollout and cost controls.

**Important:** Production-scale design is not a claim that FinSight
currently has production traffic. Numerical values in this document are
example starting points. Load-test results, provider quotas, business
requirements and operational experience must determine final settings.

## 2. Design principles

1.  **Scale stateless compute horizontally.** API instances should not
    depend on local process memory for durable state.
2.  **Keep PostgreSQL authoritative.** Caches and queues are not the
    source of truth for financial records.
3.  **Protect the voice path.** Long-running imports, reports and
    forecasts must not starve interactive voice requests.
4.  **Bound every resource.** Requests, uploads, tool calls, model
    context, audio buffers, retries and jobs need limits.
5.  **Prefer graceful degradation.** If speech synthesis fails, return
    text; if a forecast is unavailable, still provide verified
    historical analytics.
6.  **Make operations observable.** Every important request and
    background job should have correlation and trace identifiers.
7.  **Use idempotency for retries.** A timeout must not cause duplicate
    imports, notifications or mutations.
8.  **Avoid premature infrastructure.** Introduce Redis, queues, read
    replicas, partitioning and service extraction when measurements
    justify them.
9.  **Separate tenant data.** Every cache key, job, query and event must
    preserve user ownership.
10. **Fail closed for financial authorization.** Infrastructure
    degradation must never weaken access controls.

------------------------------------------------------------------------

## 3. Production reference architecture

``` mermaid
flowchart TB
    U[Web and Slack Clients] --> EDGE[DNS / TLS / WAF / Load Balancer]
    EDGE --> API[Stateless FastAPI Replicas]
    EDGE --> WS[Voice WebSocket Gateway Replicas]

    API --> AUTH[Authentication and Rate Limits]
    WS --> AUTH

    API --> PG[(PostgreSQL Primary)]
    WS --> PG
    API --> CACHE[(Redis Cluster or Managed Redis)]
    WS --> CACHE

    API --> OBJ[Private Object Storage]
    API --> Q[Durable Job Queue]
    Q --> W[Worker Pool]
    W --> PG
    W --> OBJ

    WS --> STT[Gnani Prisma]
    WS --> LLM[Reasoning Provider]
    WS --> TTS[Gnani Timbre]

    API --> OBS[Metrics / Logs / Traces]
    WS --> OBS
    W --> OBS
    PG --> OBS
```

Logical separation does not require separate microservices at the start.
API and voice gateway can initially share one FastAPI codebase and
deployment, then be deployed as separate process roles when independent
scaling becomes necessary.

### 3.1 Runtime roles

  -----------------------------------------------------------------------
  Runtime role            Responsibilities        Scaling signal
  ----------------------- ----------------------- -----------------------
  HTTP API                CRUD, dashboard,        Request rate, latency,
                          imports, budgets,       CPU
                          reports                 

  Voice gateway           WebSocket sessions and  Concurrent sessions,
                          provider orchestration  event-loop lag, memory

  Worker                  Imports, forecasts,     Queue depth, job age,
                          reports, scheduled      execution time
                          rules                   

  Scheduler               Enqueue periodic work   Schedule lag and missed
                                                  runs

  PostgreSQL              Durable financial state Query latency, IOPS,
                                                  locks, connections

  Redis                   Cache, counters,        Memory, latency,
                          ephemeral coordination  evictions, connection
                                                  count
  -----------------------------------------------------------------------

The scheduler should enqueue durable jobs rather than performing
long-running work itself.

------------------------------------------------------------------------

## 4. Capacity planning and scaling model

### 4.1 Begin with workload characterization

Estimate and then measure: - Registered users. - Daily active users. -
Requests per active user. - Peak requests per second. - Concurrent voice
sessions. - Average voice-turn duration. - Audio bytes per session. -
CSV import size and rows. - Transactions per user. - Dashboard query
mix. - Background job volume. - Provider requests and monthly speech
minutes.

A useful first-order estimate:

`Peak API RPS = active users in peak window × average requests per user in that window / window seconds`

Concurrent voice sessions can be estimated with Little's Law:

`Concurrent sessions ≈ session arrival rate × average session duration`

These estimates guide load tests; they are not a substitute for
measurements.

### 4.2 Capacity dimensions

  -----------------------------------------------------------------------
  Component                           Primary capacity constraint
  ----------------------------------- -----------------------------------
  FastAPI HTTP                        CPU, memory, request concurrency

  Voice gateway                       Open WebSockets, buffers, provider
                                      sockets, event-loop latency

  Gnani APIs                          Account quota, concurrency,
                                      provider latency

  Reasoning model                     Token throughput, concurrency,
                                      context size, provider quota

  PostgreSQL                          CPU, memory, IOPS, locks, active
                                      connections

  Redis                               Memory, network, hot keys and
                                      command latency

  Workers                             Queue depth, job duration,
                                      CPU/memory

  Object storage                      Upload/download throughput and
                                      retention
  -----------------------------------------------------------------------

### 4.3 Example load-test progression

Use staged profiles, not a claim of current capacity:

1.  Local correctness: one user, deterministic fixture.
2.  Integration: 5--10 concurrent users.
3.  MVP load: 20--50 concurrent web users and 3--5 concurrent voice
    sessions.
4.  Pre-production: increase concurrency in steps while measuring
    p95/p99 latency, errors and saturation.
5.  Production: set capacity and autoscaling thresholds from observed
    traffic plus an agreed headroom target.

Test provider limits separately. Gnani account credits or concurrency
quotas may become the bottleneck before application infrastructure.

### 4.4 Autoscaling

Scale stateless API and worker replicas independently.

Possible signals: - API: CPU, request concurrency, p95 latency. - Voice:
active sessions per replica, event-loop lag, memory per session. -
Worker: oldest queued job age, queue depth, worker utilization.

Avoid scaling solely on CPU. WebSocket workloads may be memory- or
connection-bound while CPU remains low.

Use minimum warm capacity for latency-sensitive voice traffic if cold
starts or model/provider connection setup materially increase
first-response latency.

------------------------------------------------------------------------

## 5. API rate limiting and abuse control

### 5.1 Why rate limits are required

Rate limits protect: - User experience and fair usage. - Gnani and
reasoning-provider quotas. - Expensive analytics and report
generation. - Authentication endpoints. - Upload and WebSocket resource
consumption. - Backend and database availability.

### 5.2 Layered rate limits

Apply limits at several levels:

1.  Edge/WAF: IP-level abuse and volumetric protection.
2.  Authentication: login, OTP or token issuance attempts.
3.  Application: authenticated user and endpoint limits.
4.  Provider adapter: Gnani/model-specific concurrency and request
    quotas.
5.  Job system: per-user queued and running job limits.
6.  Voice session: concurrent sessions, audio duration and turn
    frequency.

IP limits must not be the only control because multiple users can share
an IP and one user can change networks.

### 5.3 Example initial policy

These values are illustrative defaults for load testing and must be
tuned:

  ------------------------------------------------------------------------
  Operation                   Example starting limit Additional guard
  --------------------- ---------------------------- ---------------------
  General read API          120 requests/minute/user Burst allowance

  Financial analytics        30 requests/minute/user Maximum date range

  CSV import creation                    5/hour/user File size and row cap

  Report generation                      5/hour/user One active job/type

  Voice sessions                   2 concurrent/user Session idle timeout

  Voice turns                      30/minute/session Audio duration cap

  Login attempts               5/minute/account + IP Progressive delay
                                            controls 

  Slack events                  Provider retry-aware Signature and event
                                                     deduplication
  ------------------------------------------------------------------------

Do not blindly copy these limits into production. Set them using product
requirements, provider quotas and observed abuse patterns.

### 5.4 Rate-limiting algorithm

Token bucket is a useful default because it permits small bursts while
enforcing a sustained rate.

For a bucket with capacity `B` and refill rate `r` tokens/second:

`tokens_now = min(B, tokens_previous + r × elapsed_seconds)`

A request is admitted if at least one token is available; otherwise
reject or defer it.

Possible Redis key:

`rate:{scope}:{subject}:{window}`

Use an atomic Lua script or another atomic Redis operation so concurrent
API replicas cannot race while updating the same bucket.

For simpler low-volume endpoints, a fixed window may be sufficient.
Sliding-window counters or token buckets are preferable where boundary
bursts matter.

### 5.5 Rate-limit response

Return HTTP `429 Too Many Requests` with: - Stable error code. -
`Retry-After` where meaningful. - Request/correlation ID. - No internal
quota or secret information.

WebSocket limits should use an application error event and then close
the connection with an appropriate close code when necessary.

### 5.6 Provider-level concurrency control

Maintain separate concurrency budgets for: - STT requests/streams. - TTS
requests/streams. - Reasoning-model calls.

Use bounded semaphores or distributed leases depending on whether one
process or multiple replicas share the quota. A process-local semaphore
alone cannot enforce a global provider limit across replicas.

When the provider is saturated: - Queue briefly only if the user
experience permits. - Otherwise reject gracefully with a retryable
status. - Never accumulate unbounded waiting audio or requests.

------------------------------------------------------------------------

## 6. Caching strategy

### 6.1 Cache only derived, safe-to-cache data

Potential cache candidates: - System category lists. - Public merchant
normalization dictionaries. - User dashboard aggregates. - Repeated
period summaries. - Static configuration. - Short-lived voice session
metadata. - Rate-limit counters.

Do not cache raw credentials, unrestricted statements or sensitive
payloads without a strong need and explicit TTL/access controls.

### 6.2 Cache-aside pattern

1.  API constructs a cache key.
2.  Check Redis.
3.  On hit, validate schema/version and return.
4.  On miss, query PostgreSQL/domain service.
5.  Store the derived result with a bounded TTL.
6.  Return the result.

Example:

``` python
async def get_monthly_summary(user_id, month):
    key = f"fin:v1:summary:{user_id}:{month}"

    cached = await redis.get(key)
    if cached is not None:
        return decode_summary(cached)

    result = await analytics_service.monthly_summary(
        user_id=user_id,
        month=month,
    )

    await redis.set(
        key,
        encode_summary(result),
        ex=300,
    )
    return result
```

This is illustrative pseudocode; actual serialization, schema validation
and Redis client usage belong in the implementation.

### 6.3 Cache key design

Always include: - Tenant/user ID. - Resource or query type. - Normalized
parameters. - Currency where relevant. - Schema/cache version.

Example:

`fin:v2:dashboard:{user_id}:{currency}:{period_start}:{period_end}`

Never use a cache key that can return one user's financial result to
another user.

### 6.4 TTL guidance

  ------------------------------------------------------------------------
  Data                                   Example TTL Reason
  --------------------- ---------------------------- ---------------------
  System categories                 1 hour--24 hours Rarely changes

  Merchant dictionary                    1--24 hours Controlled shared
                                                     data

  Dashboard aggregate                   1--5 minutes Financial writes
                                                     invalidate it

  Transaction query              Avoid or very short Frequently changes
  result                                             and can be sensitive

  Voice session                   Seconds to minutes Ephemeral
  metadata                                           

  Forecast result       Until input/model changes or Expensive derived
                                    scheduled expiry computation

  Rate-limit counter                Policy-dependent Enforcement state
  ------------------------------------------------------------------------

TTL is a safety net, not the sole invalidation strategy.

### 6.5 Invalidation

After a successful transaction import or correction: - Invalidate
dashboard summaries for affected user/date ranges. - Invalidate category
and merchant aggregates. - Mark forecasts stale if their training data
changed. - Re-evaluate affected budget thresholds and recurring
patterns.

Use versioned cache namespaces or user-level data version counters to
avoid complex wildcard deletion.

### 6.6 Stampede protection

When a popular key expires, many requests may recompute it
simultaneously.

Mitigations: - Per-key short-lived lock. - Request
coalescing/single-flight. - TTL jitter. - Stale-while-revalidate for
non-critical dashboard data. - Precompute selected summaries after
imports.

Do not serve stale values for security-sensitive authorization or
financial mutations. For financial results, expose freshness metadata
where stale-while-revalidate is used.

### 6.7 Cache consistency policy

PostgreSQL remains authoritative. A successful mutation must not depend
on Redis availability. If invalidation fails, record a retryable
invalidation event or use a version-based key strategy. Do not silently
assume cached financial summaries are fresh.

------------------------------------------------------------------------

## 7. Database connection management and performance

### 7.1 Connection pooling

Use SQLAlchemy connection pooling with: - Bounded pool size. - Bounded
overflow. - Connection acquisition timeout. - `pool_pre_ping` or
equivalent stale-connection detection. - Appropriate connection recycle
policy. - Short-lived sessions scoped to requests/jobs.

Do not create a new database engine per request.

### 7.2 Connection budget

For multiple replicas, estimate:

`Potential DB connections = API replicas × pool size + worker replicas × worker pool size + admin/monitoring connections`

This total must remain below the database connection budget with
reserved capacity for migrations, administration and failover.

If replica count increases, reduce per-process pool sizes or use a
database connection pooler such as PgBouncer where appropriate.

### 7.3 Query design

-   Use SQL aggregation for common financial summaries.
-   Select only required columns.
-   Paginate transaction listings.
-   Avoid N+1 ORM patterns.
-   Use explicit date ranges and indexed predicates.
-   Parameterize all values.
-   Inspect `EXPLAIN (ANALYZE, BUFFERS)` for slow queries in a safe
    environment.
-   Avoid loading a user's entire transaction history into application
    memory for ordinary dashboard requests.

### 7.4 Transaction boundaries

-   Keep database transactions short.
-   Do not hold a DB transaction open while calling Gnani, an LLM or
    Slack.
-   Use optimistic concurrency/version fields for conflicting edits
    where needed.
-   Use row locks only for short critical sections.
-   Apply unique constraints for idempotency and ownership invariants.

### 7.5 Read replicas

Consider read replicas only when: - Read load is substantial. - Query
optimization and indexes are insufficient. - The application can
tolerate replication lag.

Do not route read-after-write financial requests to a lagging replica
unless consistency behavior is explicit. Mutations and immediate
confirmation reads should use the primary or a consistency-aware
strategy.

### 7.6 Partitioning and archival

Do not partition the initial 15K--20K synthetic transaction dataset.

At larger scale, evaluate: - Time-based transaction partitioning. -
Retention/archival policy. - Index size and vacuum behavior. - Partition
pruning. - Foreign-key and uniqueness implications.

Partition only after query plans and operational costs justify it.

------------------------------------------------------------------------

## 8. Asynchronous jobs and queue architecture

### 8.1 Tasks that should be asynchronous

-   Large CSV imports.
-   Bulk categorization.
-   Forecast generation.
-   Batch anomaly detection.
-   Recurring-payment detection.
-   PDF/report generation.
-   Scheduled summaries.
-   Notification delivery.

Small interactive analytics should remain synchronous when they reliably
complete within the API latency budget.

### 8.2 Job lifecycle

``` mermaid
stateDiagram-v2
    [*] --> Queued
    Queued --> Running
    Running --> Succeeded
    Running --> RetryScheduled
    RetryScheduled --> Queued
    Running --> Failed
    Queued --> Cancelled
    Running --> Cancelled
    Succeeded --> [*]
    Failed --> [*]
    Cancelled --> [*]
```

Persist job state in PostgreSQL or a durable job system. A broker
message alone should not be the only record that a critical import
exists.

### 8.3 Job envelope

Each job should include: - `job_id` - `job_type` - `user_id` -
`schema_version` - Validated parameters or references -
`idempotency_key` - `created_at` - `attempt` - `trace_id`

Do not put raw financial statements or secrets into broker payloads.
Pass private object-storage references and retrieve them under
authorization.

### 8.4 Queue separation

Use separate queues or worker pools for: - Interactive/urgent
notifications. - CSV imports. - Forecasting and ML workloads. - Reports
and scheduled batch work.

This prevents a large import from delaying a time-sensitive
voice-related notification or small job.

### 8.5 Retry and dead-letter handling

-   Retry only transient failures.
-   Use exponential backoff with jitter.
-   Set maximum attempts and maximum job age.
-   Move exhausted jobs to a dead-letter/failure state.
-   Record safe failure reasons and allow controlled operator/user
    retry.
-   Ensure retry does not duplicate side effects.

Example backoff:

`delay = min(max_delay, base_delay × 2^attempt) + random_jitter`

The actual policy should be per job type.

### 8.6 Transactional outbox

For important events such as `import.completed` or
`budget.threshold_crossed`, consider the transactional outbox pattern:

1.  Commit domain state and an outbox event in the same PostgreSQL
    transaction.
2.  A publisher reads unpublished outbox rows.
3.  Publish to the queue/event transport.
4.  Mark published.
5.  Consumers deduplicate using event ID.

This avoids the dual-write failure where the database commit succeeds
but event publication fails.

------------------------------------------------------------------------

## 9. Idempotency and distributed consistency

### 9.1 Idempotent operations

Require idempotency for: - Import commit. - Report generation request. -
Notification creation/delivery. - Slack event processing. - Budget/goal
mutations where clients may retry. - Background job submission.

### 9.2 Idempotency key flow

1.  Client creates or receives a unique key.
2.  Backend scopes it to user and operation.
3.  Database unique constraint prevents duplicate accepted operations.
4.  Backend stores operation status and result reference.
5.  A retry returns the existing operation state/result rather than
    repeating side effects.

Do not trust a key without scoping it to authenticated user and
operation type.

### 9.3 Exactly-once processing

Do not promise exactly-once delivery across distributed systems. Design
for at-least-once delivery plus idempotent consumers and durable
deduplication.

### 9.4 Event ordering

Where order matters, include: - Aggregate/entity ID. - Event sequence or
version. - Event timestamp. - Event ID.

Consumers should detect stale/out-of-order updates. Do not rely on
timestamps alone for strict ordering.

------------------------------------------------------------------------

## 10. Resilience: timeouts, retries and circuit breakers

### 10.1 Timeouts

Set explicit timeouts for: - Database acquisition and queries. - Gnani
STT and TTS operations. - Reasoning-model requests. - Slack calls. -
Object storage. - Queue operations.

Timeouts should be based on measured latency and provider contracts.
Avoid unlimited waits.

### 10.2 Retry policy

Retry only when: - Failure is plausibly transient. - Operation is safe
to retry or idempotent. - Deadline remains. - Provider quota and user
experience permit it.

Do not retry: - Invalid input. - Authentication/authorization failure. -
Unsupported language/model. - Deterministic validation errors. -
Non-idempotent mutation without deduplication.

### 10.3 Circuit breaker

Use a circuit breaker around unstable external dependencies.

States: - **Closed:** calls flow normally; failures are counted. -
**Open:** calls fail fast after threshold; recovery wait begins. -
**Half-open:** limited probe calls test recovery.

Track breakers independently for STT, TTS, reasoning, Slack and object
storage.

A circuit breaker protects the application; it does not replace provider
rate limiting or request timeouts.

### 10.4 Bulkheads

Separate concurrency pools for: - STT. - TTS. - Reasoning calls. - CSV
imports. - Forecast jobs. - Reports.

A saturated report worker pool should not consume every connection or
task slot required by voice requests.

### 10.5 Graceful degradation

  -----------------------------------------------------------------------
  Dependency failure                  Degraded behavior
  ----------------------------------- -----------------------------------
  STT unavailable                     Offer text input

  TTS unavailable                     Return text answer

  Reasoning model unavailable         Offer supported deterministic flows
                                      or clear temporary error

  Forecast service unavailable        Show verified historical analytics

  Redis unavailable                   Bypass cache; enforce safe fallback
                                      limits or reject operations needing
                                      distributed coordination

  Queue unavailable                   Reject/defer new durable jobs;
                                      preserve request state

  Slack unavailable                   Keep web app operational and retry
                                      eligible notifications

  Object storage unavailable          Reject uploads/report generation
                                      without corrupting database state
  -----------------------------------------------------------------------

Never return a guessed financial value as a fallback.

------------------------------------------------------------------------

## 11. Voice concurrency and real-time resource control

Voice sessions are long-lived and resource-intensive compared with
ordinary HTTP requests.

### 11.1 Session admission

At session start: - Authenticate user. - Enforce per-user and global
concurrent-session caps. - Verify provider capacity budget. - Allocate
session/request IDs. - Apply idle and maximum session duration. -
Negotiate audio format and maximum frame size.

Reject excess sessions cleanly rather than accepting connections that
cannot be served.

### 11.2 Backpressure

-   Bound inbound audio buffers.
-   Bound provider event queues.
-   Do not accumulate unlimited TTS audio.
-   Pause or reject input if downstream processing cannot keep up.
-   Limit maximum utterance duration and total bytes.
-   Discard stale events from cancelled requests.

### 11.3 WebSocket scaling

-   Use a load balancer that supports WebSocket upgrade and long-lived
    connections.
-   Configure idle timeouts and keepalive behavior.
-   Do not assume requests from one user always reach the same replica.
-   Store shared session ownership/leases in Redis only if cross-replica
    coordination is needed.
-   Use connection affinity only when required by the chosen session
    design; it is not a replacement for shared state.

### 11.4 Session cleanup

On disconnect, timeout or cancellation: - Cancel pending provider
tasks. - Close provider sockets. - Release concurrency permits. - Clear
audio buffers. - Mark request state terminal. - Expire ephemeral session
data. - Record a safe completion/failure event.

### 11.5 Audio and transcript privacy

-   Do not retain raw audio by default.
-   Retain transcripts only when necessary and under a documented
    policy.
-   Redact sensitive values from logs.
-   Avoid sending unnecessary transaction details to the reasoning
    model.
-   Provide a clear user-facing explanation of data handling.

------------------------------------------------------------------------

## 12. Security and tenant isolation at scale

### 12.1 Defense in depth

-   TLS in transit.
-   Encryption at rest for database, object storage and backups.
-   Managed secrets and rotation.
-   Strong authentication and short-lived session credentials.
-   Role/ownership checks in application services.
-   Database constraints for ownership consistency.
-   Optional PostgreSQL row-level security (RLS) as defense in depth,
    not a substitute for application authorization.
-   Private object storage and signed, short-lived download URLs.
-   Audit records for sensitive operations.

### 12.2 PostgreSQL row-level security

If RLS is adopted: - Set tenant context transaction-locally. - Ensure
pooled connections cannot leak previous tenant context. - Use
`SET LOCAL` or equivalent within a transaction. - Test missing context
and connection reuse. - Avoid granting application roles bypass-RLS
privileges unless explicitly required. - Keep application authorization
checks as well.

### 12.3 Sensitive-data minimization

-   Do not collect full bank account/card credentials.
-   Mask account references.
-   Keep raw statement retention configurable.
-   Keep logs free of full transaction descriptions where possible.
-   Do not include secrets or full statements in LLM prompts.
-   Restrict support/admin access and audit it.

### 12.4 Abuse and cost controls

-   Per-user quotas.
-   Upload row/size limits.
-   Tool-call budgets per turn.
-   Maximum model context and output tokens.
-   Maximum voice duration.
-   Provider spend monitoring.
-   Anomaly alerts for unusual usage.
-   Global kill switches for expensive integrations.

------------------------------------------------------------------------

## 13. Observability and operational telemetry

### 13.1 Three pillars

**Metrics** - Request rate, errors and latency. - Active voice
sessions. - Provider latency and failure rate. - DB pool usage and query
duration. - Cache hit/miss/eviction rate. - Queue depth and oldest job
age. - Import throughput and row failures. - Forecast/anomaly job
duration. - Notification delivery rate.

**Structured logs** - Timestamp and severity. - Service/runtime role. -
Request ID and trace ID. - User ID in pseudonymous/internal form where
appropriate. - Operation and status. - Provider/model identifier. -
Duration and safe error code.

Never log API keys, auth headers, raw audio, full CSV contents or
unnecessary financial details.

**Distributed traces** Trace: - HTTP request. - Voice WebSocket turn. -
STT call. - Reasoning call. - Tool execution. - Database query. - TTS
call. - Job enqueue and worker execution. - Slack delivery.

### 13.2 Example metrics

  Metric                                Purpose
  ------------------------------------- ------------------------------
  `http_requests_total`                 Traffic and error rates
  `http_request_duration_seconds`       API latency distribution
  `voice_active_sessions`               Concurrent voice load
  `voice_turn_duration_seconds`         End-to-end voice performance
  `provider_request_duration_seconds`   Gnani/model latency
  `provider_errors_total`               Provider reliability
  `db_pool_checked_out`                 Connection saturation
  `db_query_duration_seconds`           Slow query detection
  `cache_hit_ratio`                     Cache effectiveness
  `jobs_pending`                        Queue backlog
  `job_oldest_age_seconds`              Queue delay
  `csv_import_rows_total`               Import throughput
  `notification_delivery_total`         Notification success/failure

Avoid high-cardinality metric labels such as raw user IDs, transaction
IDs or arbitrary merchant names.

### 13.3 Correlation

A single user action should be traceable with: - `request_id` -
`trace_id` - `session_id` for voice - `job_id` for background work -
provider request ID where returned

Do not use these identifiers as authorization credentials.

------------------------------------------------------------------------

## 14. SLOs, SLIs and error budgets

Define service-level indicators before committing to service-level
objectives.

Candidate SLIs: - Successful API request ratio. - p95/p99 latency by
endpoint class. - Successful import completion ratio. - Voice turn
completion ratio. - Time to first audio. - Financial query correctness
on regression fixtures. - Notification delivery delay. - Data durability
and recovery success.

Example initial objectives for discussion---not a production promise:

  -----------------------------------------------------------------------
  SLI                                 Illustrative target
  ----------------------------------- -----------------------------------
  Non-provider API availability       99.5% monthly

  Dashboard API p95                   Under 500 ms for cached/typical
                                      queries

  Import job success                  99% for valid supported files

  Voice turn completion               98% excluding user
                                      cancellation/provider-wide outage

  Voice first-audio p95               Establish baseline, then set target

  Financial regression suite          100% pass before release
  -----------------------------------------------------------------------

Separate provider-dependent voice availability from application
availability. A Gnani outage should be visible as a provider dependency
incident, not concealed in the overall metric.

Error budgets can guide release decisions: if reliability degrades,
prioritize stability over new feature deployment.

------------------------------------------------------------------------

## 15. Alerting and incident response

### 15.1 Alert examples

-   API error ratio exceeds threshold.
-   p95 latency breaches objective.
-   PostgreSQL connections approach configured maximum.
-   Database storage or replication lag becomes unsafe.
-   Voice provider failure rate spikes.
-   STT/TTS quota or credit is nearly exhausted.
-   Queue oldest-job age exceeds allowed delay.
-   Import failure rate rises.
-   Notification backlog grows.
-   Repeated cross-tenant authorization failures occur.

Alerts should be actionable and include a runbook link or first
diagnostic step. Avoid alerting on every transient error.

### 15.2 Incident response sequence

1.  Detect and acknowledge.
2.  Identify affected component and user impact.
3.  Mitigate: disable a failing integration, shed load or switch to text
    fallback.
4.  Preserve logs/traces without collecting unnecessary sensitive data.
5.  Restore service.
6.  Verify data integrity and queued work.
7.  Communicate status where appropriate.
8.  Conduct a blameless post-incident review.
9.  Add regression tests and update runbooks.

### 15.3 Operational runbooks

Maintain concise runbooks for: - PostgreSQL outage/failover. - Redis
outage. - Gnani STT/TTS outage. - Reasoning-provider outage. - Queue
backlog. - Failed CSV import. - Stuck voice sessions. - Secret
rotation. - Data restoration. - Accidental data exposure.

------------------------------------------------------------------------

## 16. Backups, disaster recovery and data durability

### 16.1 PostgreSQL

Production configuration should include: - Automated backups. -
Point-in-time recovery where supported. - Backup encryption. - Defined
retention. - Periodic restore drills. - Monitoring of backup completion
and age.

### 16.2 Object storage

-   Enable versioning where appropriate.
-   Apply lifecycle/retention policies.
-   Encrypt at rest.
-   Keep objects private.
-   Back up or replicate metadata required to locate objects.
-   Ensure deletion policy covers both object and database references.

### 16.3 Recovery objectives

Define: - **RPO:** maximum acceptable data loss window. - **RTO:**
maximum acceptable recovery time.

Do not claim values until the selected hosting/database plan can meet
them and restore drills confirm them.

### 16.4 Recovery procedure

1.  Declare incident and freeze risky writes if needed.
2.  Restore PostgreSQL to the approved recovery point.
3.  Restore or verify object storage.
4.  Reconcile imports/jobs/events that were in-flight.
5.  Rebuild disposable caches.
6.  Verify tenant isolation and key financial invariants.
7.  Resume traffic gradually.
8.  Record recovery timeline and gaps.

Redis should be reconstructible. Losing cache data must not mean losing
financial records.

------------------------------------------------------------------------

## 17. Deployment, releases and configuration

### 17.1 Environments

-   Local development.
-   CI/test.
-   Staging/integration.
-   Production.

Each environment uses separate credentials, databases, buckets and
provider keys where available.

### 17.2 Release pipeline

1.  Run formatting, linting, type checks and unit tests.
2.  Run integration tests and migrations against an ephemeral database.
3.  Build immutable container images.
4.  Scan dependencies and images.
5.  Deploy to staging.
6.  Run smoke and provider contract tests.
7.  Deploy gradually to production.
8.  Monitor key SLIs.
9.  Roll back application version if health degrades.

### 17.3 Database migrations

-   Use Alembic.
-   Prefer backward-compatible expand-and-contract migrations.
-   Avoid destructive schema changes in the same release that removes
    old application compatibility.
-   Back up before risky migrations.
-   Test migration and rollback/recovery procedures.
-   Do not assume application rollback automatically reverses a schema
    migration.

### 17.4 Feature flags

Use flags for: - New reasoning model. - New STT/TTS mode. - Experimental
anomaly detector. - Forecast model changes. - Slack notification
rollout. - Expensive report features.

Flags should be server-side, scoped and auditable. A feature flag is not
an authorization control.

------------------------------------------------------------------------

## 18. Cost management

Production cost is driven by: - Speech minutes and concurrent provider
sessions. - Reasoning-model tokens. - Database compute/storage. - Redis
and queue infrastructure. - Object storage and report retention. -
Worker CPU/memory. - Observability ingestion.

Controls: - Keep voice responses concise. - Avoid unnecessary LLM calls
for deterministic analytics. - Limit context and tool output. - Cache
safe repeated aggregates. - Batch imports and background analysis. -
Enforce per-user quotas. - Monitor cost per active user and per voice
turn. - Set budget alerts and provider kill switches. - Expire temporary
files and ephemeral session state.

Do not optimize for token cost at the expense of financial correctness
or authorization.

------------------------------------------------------------------------

## 19. Technology choices and maturity gates

  -----------------------------------------------------------------------
  Capability              MVP                     Production evolution
                                                  trigger
  ----------------------- ----------------------- -----------------------
  API runtime             FastAPI modular         Separate API/voice
                          monolith                process roles when
                                                  scaling differs

  Database                PostgreSQL              Pooler, replicas,
                                                  partitioning when
                                                  measured

  Cache                   Optional Redis          Add when repeated
                                                  reads/session
                                                  coordination justify it

  Queue                   Durable worker          Separate queues and
                          mechanism when needed   worker pools by
                                                  workload

  Rate limits             App-level bounded       Distributed token
                          limits                  bucket and edge/WAF
                                                  controls

  Observability           Structured logs and     Distributed tracing,
                          basic metrics           SLO dashboards and
                                                  alerting

  Deployment              Docker-based deployment Multi-replica rollout
                                                  and autoscaling

  File storage            Private object storage  Lifecycle, versioning
                                                  and retention
                                                  automation

  ML                      Baseline                Model registry,
                          rules/statistical       monitoring and
                          models                  retraining only when
                                                  justified
  -----------------------------------------------------------------------

### 19.1 Do not add by default

-   Kubernetes.
-   Kafka.
-   Service mesh.
-   Multiple databases.
-   Dedicated vector database.
-   Complex event streaming platform.
-   Multi-region active-active architecture.

Introduce these only when a concrete requirement, measured bottleneck or
operational need justifies the cost.

------------------------------------------------------------------------

## 20. Production readiness checklist

### Traffic and resource controls

-   [ ] Request and upload limits configured.
-   [ ] Provider concurrency limits configured.
-   [ ] Voice session and audio buffer limits configured.
-   [ ] Worker queues bounded and monitored.
-   [ ] Database connection budget calculated.
-   [ ] Load test completed at an agreed profile.

### Data and consistency

-   [ ] PostgreSQL backups and restore drill completed.
-   [ ] Idempotency enforced for retryable operations.
-   [ ] Outbox or equivalent reliable event publication used where
    needed.
-   [ ] Cache invalidation tested after transaction changes.
-   [ ] User isolation tested across API, cache, jobs and Slack.
-   [ ] Data retention and deletion workflows defined.

### Resilience

-   [ ] Provider timeouts configured.
-   [ ] Retry policies bounded and jittered.
-   [ ] Circuit breakers and bulkheads tested.
-   [ ] Graceful text fallback works.
-   [ ] Queue recovery and dead-letter handling tested.
-   [ ] WebSocket disconnect cleanup tested.

### Security

-   [ ] TLS and encryption at rest enabled.
-   [ ] Secrets managed and rotatable.
-   [ ] Logs redact sensitive data.
-   [ ] RLS considered and tested if enabled.
-   [ ] Signed/private object access enforced.
-   [ ] Rate limits and abuse controls tested.

### Operations

-   [ ] Metrics, logs and traces correlated.
-   [ ] SLOs and alerts defined.
-   [ ] Runbooks available.
-   [ ] Staging smoke tests automated.
-   [ ] Rollback procedure tested.
-   [ ] RPO/RTO documented and validated.
-   [ ] Cost monitoring and provider usage alerts enabled.

------------------------------------------------------------------------

## 21. FinSight implementation roadmap

### Stage 1 --- Hackathon MVP

-   Modular FastAPI backend.
-   PostgreSQL.
-   Direct Gnani Prisma/Timbre adapters.
-   Custom Python voice orchestrator.
-   Shared financial tool registry.
-   CSV ingestion.
-   Core analytics, budgets and basic anomaly rules.
-   Simple forecast baseline.
-   React dashboard and voice UI.
-   Slack integration for selected queries.
-   Structured logs and essential tests.

### Stage 2 --- Hardened beta

-   Redis for distributed rate limits/session coordination if needed.
-   Durable worker queue for imports, forecasts and reports.
-   Cache-aside for measured hot queries.
-   Provider timeouts, retries and circuit breakers.
-   Better observability and load testing.
-   Backup/restore drills.
-   User data export and deletion workflows.
-   Security review and cross-tenant testing.

### Stage 3 --- Production scale

-   Independent scaling of HTTP, voice and worker roles.
-   Managed connection pooling.
-   Autoscaling based on concurrency and queue age.
-   Read replicas or partitioning only if justified.
-   Distributed tracing and formal SLO/error budgets.
-   Outbox/event-driven notification delivery.
-   Advanced incident response and disaster recovery.
-   Cost governance and provider failover strategy.

**End of `system_design.md`.**
