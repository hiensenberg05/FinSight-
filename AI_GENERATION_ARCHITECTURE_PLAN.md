# FinSight AI Generation Architecture Plan

**Status:** Implementation in progress; first generation-path changes are in place  
**Scope:** Request understanding, intent and tool planning, grounded answer generation, response validation, prompts, and generation evals  
**Out of scope:** Voice transport, STT/TTS providers, audio streaming, Slack delivery, UI redesign, database redesign, and autonomous financial actions

## 1. Goal

Make every generated financial answer specific to the authenticated user's request and verified tool results. The model may interpret language, select a supported capability, resolve conversational references, and explain returned facts. Application code remains responsible for permissions, financial calculations, data freshness, evidence, and deciding whether the answer is supported.

The target is a small, inspectable generation pipeline with one authoritative route from request to final answer. It should fail clearly when it cannot establish a supported intent or sufficient evidence. It must not fill gaps with demo values or plausible-sounding claims.

## 2. Current code map and problems to address

| Concern | Current location | Observed issue |
|---|---|---|
| Turn routing and generation | `backend/app/voice_agent/react_agent.py` | Combines intent routing, deterministic planning, optional Gemini planning, tool execution, response composition, visual payloads, and fallback answers. |
| Intent classification | `backend/app/voice_agent/intent_router.py` | Rule-based intent handling is mixed with history-dependent routing; needs a documented taxonomy and typed result contract. |
| Tool definitions and execution | `backend/app/voice_agent/tool_definitions.py`, `tool_registry.py` | Financial tools exist, but some return substituted values or demo-specific periods, making empty data look verified. |
| LLM answer generation | `react_agent.py`, `adapters/reasoning.py`, `specialized_agents.py`, `voice_prompts.py` | Multiple overlapping prompt and synthesis paths have inconsistent instructions and hard-coded persona/merchant examples. |
| Deterministic answer fallback | `react_agent.py`, `adapters/reasoning.py` | Scenario-specific response strings contain fixed financial claims and can be returned independently of actual tool output. |
| Evaluation | `backend/scripts/eval_agent_prompts.py`, `agent_prompt_evaluation_report.json`, other scripts | Existing scenarios provide a starting point, but “grounded” is not sufficiently proven by matching a plausible response or tool name. |

These locations are a migration map, not a commitment to preserve the present module boundaries. Before moving code, confirm the active call path and identify imports and tests that depend on each module.

## Implementation snapshot

- **Phase 0 — partial:** The active path is `VoiceOrchestrator → ReactAgent → specialized domain tool → ResponseComposer → TTS`. The duplicate planner/synthesis implementation was removed from `react_agent.py`. Existing evaluation scripts were inspected but not run.
- **Phase 1 — partial:** Scenario-specific domain answer fallbacks and multiple missing-data financial defaults were removed from the active results. Periods resolve against the current calendar month, and forecasts abstain when fewer than three months of expense history are available. Some legacy prompt text and specialized-agent copy remain outside the new domain-answer composer.
- **Phase 2 — partial:** Pydantic generation and intent-classification contracts, tool-failure outcomes, fact-path checks, and numeric-claim checks exist. Intent plans, all tool outcomes, evidence ownership, and non-numeric claim entailment are not yet uniformly validated.
- **Phase 3 — partial:** A versioned response prompt, Gemini adapter, single active domain-answer composer, and deterministic data-backed fallback are in place. Intent/planning prompt files, a formal prompt registry, an alternate provider adapter, and cleanup of legacy greeting and specialized-agent prompt text remain.
- **Phases 4–5 — not started:** No versioned eval runner, CI gates, durable traces, or full architecture-doc reconciliation has been added.

Implementation notes live in `backend/app/voice_agent/generation/README.md`. This pass did not run tests or evaluation scripts.

## 3. Proposed target structure

Keep the existing `backend/app/voice_agent` package during the first migration. Introduce focused modules incrementally rather than renaming the entire package at once:

```text
backend/app/voice_agent/
  orchestrator.py                 # Thin turn lifecycle; delegates each stage
  contracts.py                    # Typed request, intent, plan, tool, fact, answer contracts
  intent_router.py                # Supported intent taxonomy and classification interface
  context.py                      # Bounded structured conversation state and reference resolution
  planner.py                      # Plan proposal and deterministic validation
  harness.py                      # Call limits, policy checks, validation, timeouts, state transitions
  tool_registry.py                # Existing domain-tool boundary; no model-owned identity
  evidence.py                     # Evidence and provenance checks for material financial facts
  generation/
    composer.py                   # Builds response input from query, verified facts, and style
    validator.py                   # Checks answer structure and supported claims
    fallback.py                    # Safe, data-driven templates for provider/error cases
  adapters/
    reasoning.py                  # Provider-neutral generation interface
    gemini.py                     # Gemini HTTP implementation and provider response parsing
  prompts/
    README.md                     # Prompt ownership, change process, and versioning
    intent_classifier_v1.txt
    planner_v1.txt
    response_synthesis_v1.txt
    language_style_v1.txt
```

Prompt files are stable instructions only. Dynamic query, history, tool data, and evidence are passed as clearly delimited structured fields, not concatenated into a fake system instruction. Imported transaction text and user-provided content are untrusted data, never instructions.

## 4. Request-to-answer flow

1. **Receive:** Build a request context from the authenticated user, query, request ID, language preference, and bounded conversation state. User identity comes only from the authenticated server context.
2. **Understand:** Resolve supported intent, required parameters, and references to prior turns. Return `NEEDS_CLARIFICATION` for missing or ambiguous inputs. Unsupported requests receive an explicit out-of-scope outcome.
3. **Plan:** Produce a typed plan referencing only registered tools and valid arguments. The model can propose a plan; the harness validates it. Do not expose or store chain-of-thought. Store concise decision metadata such as intent, selected tool, and reason code.
4. **Authorize and execute:** Check tool permission and argument bounds, then execute deterministic domain logic with the authenticated user ID. Bound model/tool calls and timeouts. Writes stay behind the existing prepare/confirm flow and are not expanded in this phase.
5. **Verify facts:** Normalize tool output into a response fact set with period, currency, calculation definition, coverage, freshness, and evidence references. Validate evidence ownership and that it supports the facts. Distinguish valid zero results from missing data and failed queries.
6. **Compose:** Generate a concise answer from the original query and verified facts. Adapt depth to the request. Do not force the user's name, sample merchants, reassurance, unsolicited advice, or unsupported comparisons.
7. **Validate:** Reject or repair malformed output and claims that cannot be tied to supported facts. If validation cannot establish support, use a safe fallback or state the limitation. Do not treat an LLM self-check as proof.
8. **Return and trace:** Return answer, structured facts/evidence references, intent/tool outcome, prompt/model/schema versions, and request ID. Record actual stage events without sensitive raw data or hidden reasoning.

## 5. Contracts to define before refactoring

Define Pydantic contracts (names are provisional) for:

- `GenerationRequest`: request ID, authenticated user context, query, language, and bounded state reference.
- `IntentResult`: intent enum, confidence or decision status, required/missing fields, and clarification prompt key.
- `ToolPlan`: registered tool name/version and typed arguments only; no arbitrary SQL or user identity.
- `ToolOutcome`: success, empty, insufficient coverage, unsupported, or failed; structured result and safe error code.
- `FinancialFact`: metric, value in minor units where monetary, currency, period boundaries, definition/version, evidence IDs, and provenance.
- `GeneratedAnswer`: user-facing text, language, fact references, and optional presentation hints.
- `GenerationTrace`: stage timings, decisions, tool IDs, provider status, version IDs, and validation outcome.

Use explicit result states instead of overloaded `None`, zero values, or hard-coded defaults. Do not claim a result is “verified” solely because a SQL call ran; verification also requires correct scope, dates, calculation rules, and evidence where applicable.

## 6. Prompt and model policy

- Keep separate, versioned prompts for intent understanding, planning, and final synthesis; do not duplicate the same role instructions across modules.
- Prompts explain supported capabilities, clarification and abstention behavior, language matching, actual-versus-projection distinctions, and concise spoken-friendly output. Visual formatting remains a presentation-layer concern.
- Remove fixed references to Aarav, Swiggy, Zomato, Croma, HDFC, SBI, and specific amounts unless they are present in the supplied verified facts.
- Treat prompt-injection content in queries, descriptions, imported rows, and history as untrusted data. Application allowlists and authorization remain authoritative.
- Track prompt ID/version, model/provider/version, tool schema version, and orchestration version for every generated answer.
- Keep provider calls behind an adapter with bounded timeout and clear error categories. A provider failure must not trigger fabricated demo answers.
- Do not add prompt caching, a new agent framework, retrieval-augmented generation, or a second provider as part of this refactor without evidence that it solves a measured problem.

## 7. Safe fallback behavior

Fallbacks are deterministic renderers over validated tool outcomes, not scenario-specific financial scripts. They may state facts supplied by the tool result, or explain that the answer cannot be verified. They must never supply default balances, merchants, categories, dates, transaction counts, or recommendations.

Examples of valid outcomes:

- Verified value exists: render the value and its period from the fact contract.
- Valid query with no matching records: say no matching records were found for that period.
- Insufficient history: explain the missing coverage and ask for more data if appropriate.
- Tool/provider failure: say the data could not be retrieved and invite retry; do not imply zero spending.
- Unsupported request: explain the supported boundary and offer a relevant supported query.

## 8. Evaluation and release gates

Create a versioned synthetic evaluation dataset with expected intent, tool, exact arguments, clarification/abstention expectation, reference facts, evidence expectations, and safety assertions. Keep development, validation, and held-out test splits.

Measure separately:

- Intent accuracy and required-field/clarification accuracy.
- Tool selection and argument exact match.
- Deterministic numerical correctness and reconciliation.
- Evidence existence, ownership, period alignment, and fact support.
- Unsupported material claim rate and correct abstention.
- Multi-turn reference resolution, including ambiguous references.
- Language consistency for English, Hindi, and Hinglish.
- Provider failure, timeout, malformed output, and retry behavior.
- Latency and model cost by pipeline stage.

Arithmetic, permissions, evidence ownership, and action state are deterministic checks, not LLM-judge scores. Use human-calibrated model judging only for qualitative relevance, clarity, and completeness. Reports must include dataset/version, counts, skipped/failed cases, criteria, and examples. Do not report “100% grounded” without claim-to-fact checks and a documented denominator.

Initial regression gates should be conservative and explicit: zero cross-user/evidence authorization failures, zero unsupported monetary claims in the safety suite, correct behavior for empty/missing/error outcomes, and agreed thresholds for routing and language quality. Set numerical thresholds after capturing a reproducible baseline instead of inheriting aspirational values from documentation.

## 9. Phased implementation plan

### Phase 0 — Baseline and trace the live path

- Trace one API/voice text request through classifier, planner, tool, synthesis, and fallback.
- Identify unreachable/duplicate modules and existing tests/importers before moving code.
- Record a reproducible baseline on a small representative fixture set, including empty data and provider failure.
- Treat current evaluation JSON as historical evidence only until its scoring procedure is reproduced.

**Exit:** One documented active call path, known prompt inventory, and reproducible baseline.

### Phase 1 — Remove false financial truth

- Replace silent financial defaults in generation-facing tools/services with explicit outcome states.
- Remove hard-coded financial fallback strings and any fallback branch that ignores `tool_data`.
- Make safe fallback text render from typed facts or limitation/error codes.
- Add targeted regression cases for empty data, missing periods, provider failures, and follow-ups. (Tests are added when implementation begins; none were run while creating this plan.)

**Exit:** No generated or fallback financial claim can arise from a demo constant when its supporting result is absent.

### Phase 2 — Establish typed harness boundaries

- Add contracts and a thin harness around intent, plan validation, authorization, tool execution, and fact verification.
- Enforce allowed tools, input bounds, call/time limits, and explicit request states.
- Use structured context for follow-ups; clarify ambiguous references instead of mapping them to a fixed category.
- Keep all user scoping in server-side context.

**Exit:** Every request has an auditable, typed route and safe terminal outcome.

### Phase 3 — Consolidate and version generation

- Establish one response-composition path and one provider-neutral model interface.
- Move active prompts into versioned prompt files and load them through a small prompt registry.
- Separate stable instructions from structured dynamic input.
- Remove persona/merchant forcing and tune answer length, specificity, language, and voice-friendly wording against evals.

**Exit:** One active prompt path with version metadata and no duplicate synthesis behavior.

### Phase 4 — Grounding validation and eval gates

- Implement fact-reference and evidence validation for material financial claims.
- Build the versioned dataset and deterministic evaluators; include adversarial and multilingual cases.
- Re-score the stored baseline report using reproducible criteria and publish failures, not only aggregate scores.
- Add hard CI gates for authorization, numerical correctness, unsupported claims, and failure handling.

**Exit:** Prompt, model, routing, and tool changes are measured with repeatable regression gates.

### Phase 5 — Simplify and document the architecture

- Remove obsolete duplicate modules only after imports and tests confirm they are no longer part of the active path.
- Update architecture/system design docs to distinguish implemented behavior from target behavior.
- Document prompt ownership, eval workflow, trace fields, and operational failure handling.

**Exit:** Code and documentation show one consistent generation architecture and supportable ownership boundaries.

## 10. Risks and design decisions

- **Claim validation:** Free-form answer parsing is imperfect. Prefer structured answer claims/fact references for financial statements, with conservative wording when a claim cannot be matched.
- **Context:** Full transcript history can carry stale or unsafe instructions. Keep compact structured state and fetch current financial facts again for follow-ups.
- **Date semantics:** “This month” and “last month” need a single timezone and period-boundary policy; demo dataset dates must not silently redefine calendar meaning.
- **Architecture scope:** Avoid broad renames and framework adoption until Phase 0 identifies actual call paths and test dependencies.
- **Voice later:** Keep response generation channel-neutral, but do not change STT/TTS adapters, WebSocket audio protocol, voice selection, or streaming behavior in this plan's implementation phase.

## 11. Defaults applied in this first pass

- Domain answers use a structured model response with JSON fact paths, plus deterministic templates when generation is unavailable or fails validation.
- Financial defaults that could be mistaken for user data were removed from the active tool path. Synthetic database rows remain as fixtures; the runtime no longer substitutes values when a query returns no records.
- Gemini is the configured synthesis provider because it was the active model endpoint in the existing response path. `GENERATION_PROVIDER` and `GENERATION_MODEL` make that choice configurable; only the Gemini adapter is implemented so far.
- Relative periods resolve against the current calendar month. Historical synthetic data outside that month is reported as insufficient or absent coverage instead of being relabeled as current.

