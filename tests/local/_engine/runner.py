"""JSON-driven local Lambda runner.

Loads tests from a `tests.json`, builds the configured event shape, invokes
the supplied `lambda_handler` callable, and reports results to stdout.

Typical service-level glue (`run_local.py`):

    from app.main import lambda_handler  # uni-lambda
    from tests.local._engine.runner import run_from_json

    if __name__ == "__main__":
        run_from_json(
            tests_path=Path(__file__).parent / "tests.json",
            handler=lambda_handler,
        )
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .assertions import assert_response
from .event_builder import MockLambdaContext, build_event

# ANSI colors (no-op on Windows CMD without colorama; harmless otherwise)
_GREEN = "\033[0;32m"
_RED = "\033[0;31m"
_YELLOW = "\033[1;33m"
_CYAN = "\033[0;36m"
_DIM = "\033[2m"
_NC = "\033[0m"


def _load_tests(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"tests file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _parse_body(raw: Any) -> Any:
    if raw is None or raw == "":
        return None
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def _format_failure(failures: List[str]) -> str:
    return "; ".join(failures)


def run_from_json(
    tests_path: Path,
    handler: Callable[[Dict[str, Any], Any], Dict[str, Any]],
    *,
    argv: Optional[List[str]] = None,
    on_each: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> int:
    """Run all tests from a JSON file against `handler`. Returns process exit code."""
    parser = argparse.ArgumentParser(description="Run JSON-declared Lambda tests locally.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print full request/response.")
    parser.add_argument("--test", help="Run a single test by name (exact match).")
    parser.add_argument("--filter", help="Substring filter on test name.")
    parser.add_argument("--list", action="store_true", help="List test names and exit.")
    parser.add_argument("--tests", help="Override path to tests.json.")
    args = parser.parse_args(argv)

    path = Path(args.tests) if args.tests else tests_path
    data = _load_tests(path)
    defaults = data.get("defaults", {})
    all_tests = data.get("tests", [])

    if args.list:
        for t in all_tests:
            print(t.get("name", "<unnamed>"))
        return 0

    selected: List[Dict[str, Any]] = []
    for t in all_tests:
        if t.get("skip"):
            continue
        name = t.get("name", "")
        if args.test and name != args.test:
            continue
        if args.filter and args.filter.lower() not in name.lower():
            continue
        selected.append(t)

    if not selected:
        print(f"{_YELLOW}No tests match the given filters.{_NC}")
        return 0

    default_shape = defaults.get("event_shape", "apigw_v2")
    default_headers = defaults.get("headers", {})
    default_stage = defaults.get("stage")

    print(f"{_CYAN}Running {len(selected)} test(s) from {path}{_NC}\n")

    passed = failed = errored = 0
    started = time.time()

    for spec in selected:
        name = spec.get("name", "<unnamed>")
        description = spec.get("description", "")
        method = spec.get("method", "GET")
        raw_path = spec.get("path", "/")
        path_params = spec.get("path_params") or {}
        query = spec.get("query") or {}
        body = spec.get("body")
        headers = {**default_headers, **(spec.get("headers") or {})}
        shape = spec.get("event_shape", default_shape)
        stage = spec.get("stage", default_stage)

        if args.verbose:
            print(f"{_CYAN}--- {name} ---{_NC}")
            if description:
                print(f"{_DIM}{description}{_NC}")
            print(f"{method} {raw_path}")
            if path_params:
                print(f"path_params: {path_params}")
            if query:
                print(f"query: {query}")
            if body is not None:
                print("body:")
                print(json.dumps(body, indent=2, ensure_ascii=False))

        event = build_event(
            shape=shape,
            method=method,
            path=raw_path,
            query=query,
            body=body,
            headers=headers,
            path_params=path_params,
            stage=stage,
        )
        context = MockLambdaContext()

        start = time.time()
        status_code: Optional[int] = None
        parsed_body: Any = None
        error_repr: Optional[str] = None
        try:
            response = handler(event, context) or {}
            status_code = response.get("statusCode")
            raw_response_body = response.get("body", "")
            parsed_body = _parse_body(raw_response_body)
        except Exception as exc:  # noqa: BLE001 — surface any handler error
            error_repr = f"{type(exc).__name__}: {exc}"
            response = {"statusCode": 500, "body": json.dumps({"detail": error_repr})}
            if args.verbose:
                traceback.print_exc()

        duration = time.time() - start

        if error_repr is not None:
            errored += 1
            print(f"  {_YELLOW}ERROR{_NC} {name:<48} ({duration:.2f}s)")
            print(f"       {_YELLOW}{error_repr}{_NC}")
        else:
            ok, failures = assert_response(response, spec.get("expect"), parsed_body)
            if ok:
                passed += 1
                print(
                    f"  {_GREEN}PASS{_NC}  {name:<48} "
                    f"({_DIM}{status_code}, {duration:.2f}s{_NC})"
                )
            else:
                failed += 1
                print(
                    f"  {_RED}FAIL{_NC}  {name:<48} "
                    f"({_DIM}{status_code}, {duration:.2f}s{_NC})"
                )
                print(f"       {_YELLOW}{_format_failure(failures)}{_NC}")

        if args.verbose:
            print(f"status: {status_code}")
            if parsed_body is not None:
                preview = json.dumps(parsed_body, indent=2, ensure_ascii=False)
                lines = preview.splitlines()
                print("response:")
                for line in lines[:30]:
                    print(f"  {line}")
                if len(lines) > 30:
                    print(f"  {_DIM}... ({len(lines) - 30} more lines){_NC}")
            print()

        if on_each:
            on_each(
                {
                    "name": name,
                    "status_code": status_code,
                    "duration": duration,
                    "error": error_repr,
                }
            )

    total_duration = time.time() - started
    print()
    print(f"{_CYAN}Summary{_NC}")
    print(f"  {_GREEN}passed: {passed}{_NC}")
    print(f"  {_RED}failed: {failed}{_NC}")
    print(f"  {_YELLOW}errored: {errored}{_NC}")
    print(f"  total: {len(selected)}  duration: {total_duration:.2f}s")

    return 0 if (failed == 0 and errored == 0) else 1


def main_uni(handler_import_path: str, tests_path: Path) -> int:
    """Helper for `python -m` style entry points (uni-lambda)."""
    module_name, _, attr = handler_import_path.partition(":")
    if not attr:
        attr = "lambda_handler"
    module = __import__(module_name, fromlist=[attr])
    handler = getattr(module, attr)
    return run_from_json(tests_path, handler)


if __name__ == "__main__":
    # Allow direct execution: python -m tests.local._engine.runner --tests path/to/tests.json --handler app.main:lambda_handler
    parser = argparse.ArgumentParser()
    parser.add_argument("--handler", required=True, help="dotted.module:attr path to handler")
    parser.add_argument("--tests", required=True, help="path to tests.json")
    args, remaining = parser.parse_known_args()
    sys.exit(
        main_uni(
            args.handler,
            Path(args.tests),
        )
    )
