# Response generation

`ResponseComposer` is the single domain-answer generation boundary used by `ReactAgent`. The specialized agents still select and execute domain tools; their scenario-written answer text is ignored by the active turn path.

The greeting/meta fast path remains separate and still uses legacy greeting copy. It is outside the financial tool-result composer and should be consolidated in a later prompt cleanup pass.

## Data flow

1. `GenerationInput` carries the user query, selected tool, model-safe tool result, language, and a bounded recent conversation history.
2. `ResponseComposer` calls the configured provider in `providers/` with the versioned response prompt.
3. `validator.py` checks the `GeneratedAnswer` contract, fact paths, and numeric claims against the tool result.
4. Invalid output, provider failure, or missing credentials uses `fallback.py` to render a safe answer from the tool result or state the limitation.

The model does not receive authenticated user identity and cannot execute tools. Tool authorization and calculations happen before this package is called. Transaction text, query text, and history are untrusted data.

## Configuration

- `GENERATION_PROVIDER` selects the synthesis provider. The active provider is `groq`.
- `GENERATION_MODEL` selects the Groq model ID; the active model is `openai/gpt-oss-120b`.
- Set `GROQ_API_KEY` to enable model synthesis. Without it, the data-driven fallback is used.
- `REASONING_PROVIDER` and `REASONING_MODEL` mirror the active generation provider/model for older integrations; `ResponseComposer` is the runtime source of truth.
- `response_synthesis_v1.txt` is the active prompt. Increment `PROMPT_VERSION` and use a new prompt filename when changing its behavior so traces identify the version that generated an answer.

## Current limits

- Fact-path and numeric validation catch malformed citations and unsupported numeric claims. They do not prove that every non-numeric statement is logically entailed by its cited fact.
- The deterministic fallback covers common financial result shapes; unfamiliar tool outputs return a limitation instead of an invented summary.
- Prompt/model version metadata is returned with the turn result. A durable trace store and regression evaluator are still to be implemented.
- The `ReasoningAdapter` module remains as a compatibility wrapper around `ResponseComposer`.
- The current composer validates numeric tokens and cited paths, but cannot prove full semantic entailment for every free-form claim.
