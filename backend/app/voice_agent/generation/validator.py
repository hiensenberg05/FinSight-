"""Validates response shape and references against model-safe tool data."""

import re
from typing import Any, Iterable, Optional, Set

from backend.app.voice_agent.generation.contracts import GeneratedAnswer


def flatten_paths(value: Any, prefix: str = "$", paths: Optional[Set[str]] = None) -> Set[str]:
    paths = paths if paths is not None else set()
    paths.add(prefix)
    if isinstance(value, dict):
        for key, child in value.items():
            flatten_paths(child, f"{prefix}.{key}", paths)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            flatten_paths(child, f"{prefix}[{index}]", paths)
    return paths


def flatten_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from flatten_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from flatten_values(child)
    else:
        yield value


BENIGN_NUMBERS: Set[float] = {
    float(i) for i in range(101)
}.union({float(y) for y in range(2020, 2031)})


def number_tokens(value: Any) -> Set[str]:
    tokens = set()

    def _traverse(node: Any):
        if isinstance(node, (int, float)) and not isinstance(node, bool):
            val = round(float(node), 2)
            tokens.add(str(val))
            tokens.add(str(int(val)))
            if abs(val) >= 100:
                major = round(abs(val) / 100.0, 2)
                tokens.add(str(major))
                tokens.add(str(int(major)))
        elif isinstance(node, str):
            for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", node):
                c = m.group(0).replace(",", "").strip()
                try:
                    v = float(c)
                    tokens.add(str(round(v, 2)))
                    tokens.add(str(int(v)))
                except ValueError:
                    pass
        elif isinstance(node, dict):
            for k, v in node.items():
                _traverse(v)
        elif isinstance(node, (list, tuple, set)):
            for item in node:
                _traverse(item)

    _traverse(value)
    return tokens


def has_unsupported_numeric_claim(
    answer: str,
    tool_data: Any = None,
    secondary_tool_data: Any = None,
    episodic_memory: Optional[Iterable[Any]] = None,
    working_memory_context: Optional[dict] = None,
) -> bool:
    available: Set[float] = set()

    sources = [tool_data, secondary_tool_data, episodic_memory, working_memory_context]
    for src in sources:
        if src is None:
            continue
        for token in number_tokens(src):
            try:
                val = float(token.replace(",", "").strip())
                available.add(round(val, 2))
                available.add(float(int(val)))
            except ValueError:
                continue

    # Compute valid mathematical derivations from available numbers
    derived: Set[float] = set()
    base_nums = list(available)
    # Standard discretionary reduction percentages
    standard_pcts = (0.1, 0.15, 0.2, 0.25, 0.3, 0.5)

    for a in base_nums:
        # Rounding representations (e.g. 50,779 -> 50,000 or 51,000)
        if a > 1000:
            derived.add(float(round(a, -3)))
            derived.add(float(round(a, -2)))
        for p in standard_pcts:
            cut = round(a * p, 2)
            rem = round(a * (1.0 - p), 2)
            derived.add(cut)
            derived.add(rem)
            derived.add(float(int(cut)))
            derived.add(float(int(rem)))

    # Pairwise derivations (deltas, sums, percentage ratios)
    for i, a in enumerate(base_nums[:20]):
        for b in base_nums[i + 1:25]:
            delta = round(abs(a - b), 2)
            sm = round(a + b, 2)
            derived.add(delta)
            derived.add(sm)
            derived.add(float(int(delta)))
            derived.add(float(int(sm)))
            if b > 0 and a <= b * 3:
                ratio = round((a / b) * 100.0, 1)
                derived.add(ratio)
                derived.add(float(int(ratio)))
            if a > 0 and b <= a * 3:
                ratio = round((b / a) * 100.0, 1)
                derived.add(ratio)
                derived.add(float(int(ratio)))

    all_allowed = available.union(derived)

    for match in re.finditer(r"(?<![\w])\d[\d,]*(?:\.\d+)?(?![\w])", answer):
        try:
            num = float(match.group(0).replace(",", ""))
        except ValueError:
            continue
        if num in BENIGN_NUMBERS:
            continue
        # Tolerance check: within 1.0 or 2.5% relative tolerance
        matched = any(abs(num - a) <= 1.0 or abs(num - a) / max(a, 1.0) < 0.025 for a in all_allowed)
        if not matched:
            return True
    return False


def validate_answer(
    answer: GeneratedAnswer,
    tool_data: Any = None,
    secondary_tool_data: Any = None,
    episodic_memory: Optional[Iterable[Any]] = None,
    working_memory_context: Optional[dict] = None,
) -> bool:
    if not answer or not answer.answer or not answer.answer.strip():
        return False

    # Check fact_refs paths if JSONPath prefixes ($.) are specified
    if answer.fact_refs and tool_data is not None:
        valid_paths = flatten_paths(tool_data, "$")
        for ref in answer.fact_refs:
            if isinstance(ref, str) and ref.startswith("$") and ref not in valid_paths:
                return False

    if has_unsupported_numeric_claim(
        answer.answer,
        tool_data=tool_data,
        secondary_tool_data=secondary_tool_data,
        episodic_memory=episodic_memory,
        working_memory_context=working_memory_context,
    ):
        return False
    return True


def model_safe_data(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: model_safe_data(child)
            for key, child in value.items()
            if key not in {"evidence", "transaction_id", "account_reference", "source_import_id"}
        }
    if isinstance(value, list):
        return [model_safe_data(child) for child in value[:30]]
    if isinstance(value, str):
        return value[:1000]
    return value
