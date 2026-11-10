# FinSight --- Agentic AI Pipeline Quick Checkup

## Purpose

Audit the existing FinSight implementation to determine whether it is a
genuinely connected, reliable, tool-using financial agent---not merely a
chatbot with superficial tool calls. This is an audit-and-fix task, not
a redesign.

## Instructions

-   Inspect the actual repository and trace real execution paths before
    editing.
-   Preserve working functionality, database contracts and the current
    UI.
-   Distinguish implemented, partial, mocked, disconnected, missing and
    untested capabilities.
-   A function, route or UI badge does not prove an integration works.
-   Verify fixes with tests or safe local smoke tests.
-   Do not expose secrets, sensitive financial data or hidden
    chain-of-thought.
-   Do not modify production data or perform external financial actions
    during the audit.

## 1. Trace the complete request path

Trace:
`Frontend/Voice → STT → Session Manager → Intent Routing → Tool Selection → Validation → Financial Service → PostgreSQL → Evidence → Response → TTS → Frontend`

For every stage report file/module, entry point, dependencies,
input/output contract, actual connection status, errors/timeouts and
observability. Identify hardcoded responses, placeholders, mocks and
disconnected integrations.

## 2. Audit intent routing

Test whether the agent distinguishes: - Financial summaries,
category/merchant analysis and period comparisons. - Transaction search,
UPI analysis and evidence requests. - Budgets, savings goals and
recurring payments. - Anomaly investigations, forecasts and what-if
simulations. - Multi-intent requests, follow-ups, ambiguity and
unsupported requests.

Find brittle keyword routing, incorrect parameter extraction, lost
conversation context and generic fallback answers. Missing required
parameters must trigger clarification, not guessing.

## 3. Audit the tool registry

For every tool inspect its description, schema, validation, user
scoping, permissions, implementation, database connection, output
contract, evidence, errors, timeout, retry and idempotency behaviour.
Identify unused, unreachable, duplicated, broad or hardcoded tools.

The LLM must not have unrestricted SQL or direct database access. Use
registered tools, parameterized queries and deterministic financial
services.

## 4. Audit prompts and model integration

Inspect system prompts, domain instructions, intent instructions, tool
descriptions and response prompts. Find generic/contradictory
instructions, missing clarification and abstention rules, weak tool
descriptions, malformed structured outputs, provider assumptions and
duplicated prompt content.

Separate stable instructions from dynamic user context. Claim prompt
caching only if the provider supports it and runtime evidence confirms
it.

## 5. Audit the harness

Check explicit execution states, bounded tool loops, call limits,
timeouts, retries, cancellation, context/session persistence,
stale-context handling, user isolation, write idempotency, provider
failures and malformed model output recovery.

The harness---not the LLM---must enforce permissions, limits and action
policies.

## 6. Audit financial correctness and hallucination containment

Verify: - Historical values come from real database-backed tools. -
Money uses Decimal or integer minor units. - Material claims are
supported by returned facts. - Evidence IDs exist and belong to the
authenticated user. - Periods, currency and calculation rules are
explicit. - Transfers, refunds, reversals and duplicate imports are
consistent. - Forecasts are labelled as estimates. - Insufficient data
and unsupported requests produce honest limitations.

Do not use an LLM judge as the authority for arithmetic, permissions or
database truth.

## 7. Audit reactive behaviour and observability

Verify proactive alerts originate from real domain events or scheduled
evaluations, not fabricated UI activity. Inspect persistence,
idempotency, background processing, retries, user-scoped WebSocket
delivery and acknowledgement.

Ensure UI execution traces reflect actual backend events. Never expose
hidden chain-of-thought, secrets or sensitive SQL.

## 8. Code-quality smell check

Search for hardcoded financial values/users, placeholder responses, fake
connection badges, dead code, duplicate functions, broad exception
swallowing, unbounded loops, inconsistent API contracts, disconnected
components, accidental mock mode and unnecessary agent abstractions.

Prefer the smallest maintainable fix over a broad rewrite.

## 9. Required report

Return: 1. Executive status and top risks. 2. Capability matrix:
verified / partial / mocked / disconnected / missing / untested. 3.
Findings with severity (CRITICAL/HIGH/MEDIUM/LOW), file path, evidence,
impact and fix. 4. Actual integration map and broken links. 5.
Prioritized fixes. 6. Tests/commands run, results and remaining
assumptions.

## 10. Fix policy

After reporting, fix only clearly evidenced, safe issues. For each fix
explain the issue, change the smallest appropriate code surface,
add/update tests, run them and verify the real integration. Do not
silently change schemas, provider endpoints, model names or
architecture. Ask before destructive migrations or external financial
actions.

## Definition of a successful checkup

Demonstrate correct intent/tool selection, correct arguments,
authenticated user scoping, real PostgreSQL results, deterministic
calculations, verifiable evidence, safe write confirmation, real
event-driven alerts, genuine execution traces and honest
failure/unsupported handling.

The goal is to expose real weaknesses---not produce a flattering audit
report.
