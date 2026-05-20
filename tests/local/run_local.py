"""Local test entrypoint for cross-app-be (uni-lambda).

Loads tests from `tests.json`, builds synthetic API Gateway v2 events, and
invokes `app.main.lambda_handler` in-process — no uvicorn, no SAM.

Usage (from cross-app-be repo root):

    python -m tests.local.run_local                          # run all
    python -m tests.local.run_local -v                       # verbose: print bodies
    python -m tests.local.run_local --test update_product    # one test by exact name
    python -m tests.local.run_local --filter product         # substring filter
    python -m tests.local.run_local --list                   # list test names
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the service root is on sys.path before importing the handler.
SERVICE_ROOT = Path(__file__).resolve().parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(SERVICE_ROOT / ".env", override=False)

from app.main import lambda_handler  # noqa: E402

from tests.local._engine.runner import run_from_json  # noqa: E402

TESTS_PATH = Path(__file__).parent / "tests.json"


def main() -> int:
    return run_from_json(TESTS_PATH, lambda_handler)


if __name__ == "__main__":
    raise SystemExit(main())
