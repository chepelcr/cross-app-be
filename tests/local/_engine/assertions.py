"""Lightweight assertions for the JSON-driven test cases."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


def _coerce_status(expected: Union[int, Sequence[int], None]) -> Optional[List[int]]:
    if expected is None:
        return None
    if isinstance(expected, int):
        return [expected]
    return [int(s) for s in expected]


def _get_path(body: Any, jsonpath: str) -> Tuple[bool, Any]:
    """Resolve a dot-separated JSONPath-lite expression (e.g. `$.cabys.code`).

    Returns (found, value). Arrays are addressed numerically: `$.codes.0.number`.
    """
    if not jsonpath.startswith("$."):
        return False, None
    parts = jsonpath[2:].split(".")
    current = body
    for part in parts:
        if isinstance(current, list):
            try:
                idx = int(part)
            except ValueError:
                return False, None
            if idx < 0 or idx >= len(current):
                return False, None
            current = current[idx]
        elif isinstance(current, dict):
            if part not in current:
                return False, None
            current = current[part]
        else:
            return False, None
    return True, current


def assert_response(
    response: Dict[str, Any],
    expect: Optional[Dict[str, Any]],
    parsed_body: Any,
) -> Tuple[bool, List[str]]:
    """Run the `expect` block against the handler response.

    Returns (passed, failure_messages). When passed is True, failure_messages is empty.
    """
    if not expect:
        # No expectations declared — pass as long as we got a response object.
        return True, []

    failures: List[str] = []

    status = response.get("statusCode")

    expected_status = _coerce_status(expect.get("status"))
    if expected_status is not None and status not in expected_status:
        failures.append(
            f"status {status} not in expected {expected_status}"
        )

    body_assertions: Dict[str, Any] = expect.get("body") or {}
    for jsonpath, expected_value in body_assertions.items():
        found, actual = _get_path(parsed_body, jsonpath)
        if not found:
            failures.append(f"body path {jsonpath} not found")
            continue
        if actual != expected_value:
            failures.append(
                f"body {jsonpath}: expected {expected_value!r}, got {actual!r}"
            )

    contains: List[str] = expect.get("body_contains") or []
    if contains:
        if not isinstance(parsed_body, dict):
            failures.append(
                f"body_contains requires top-level object, got {type(parsed_body).__name__}"
            )
        else:
            for key in contains:
                if key not in parsed_body:
                    failures.append(f"body_contains: top-level key {key!r} missing")

    err_substring = expect.get("error_message_includes")
    if err_substring:
        # FastAPI's HTTPException renders {"detail": "..."}, others may use "message".
        candidates = []
        if isinstance(parsed_body, dict):
            for key in ("detail", "message", "error"):
                v = parsed_body.get(key)
                if isinstance(v, str):
                    candidates.append(v)
                elif isinstance(v, list):
                    candidates.extend(str(item) for item in v)
        joined = " | ".join(candidates)
        if err_substring not in joined:
            failures.append(
                f"error_message_includes: {err_substring!r} not found in {joined!r}"
            )

    return (len(failures) == 0), failures
