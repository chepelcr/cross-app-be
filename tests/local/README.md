# Local Lambda tests

JSON-declared tests that invoke `app.main.lambda_handler` in-process, without
starting `uvicorn` or SAM. Tests live in `tests.json`; the reusable engine
lives in `_engine/` and was scaffolded by the `lambda-local-test` skill.

## Run

From the cross-app-be repo root:

```bash
python -m tests.local.run_local                          # all tests
python -m tests.local.run_local -v                       # verbose: print request/response
python -m tests.local.run_local --test update_product_reported_payload
python -m tests.local.run_local --filter product
python -m tests.local.run_local --list                   # show test names
```

The runner uses your existing `.env` (loaded via `python-dotenv`) — point
`DATABASE_*` / `AWS_*` at whatever DB you want to hit.

## Add a test

Append an entry to `tests.json`. Required fields: `name`, `method`, `path`. To
reproduce a real request from DevTools, just paste the body as a JSON object
(don't stringify it) and put the path placeholders in `{braces}`.

```jsonc
{
  "name": "update_product_minimal",
  "method": "PUT",
  "path": "/api/organizations/{org_id}/products/{product_id}",
  "path_params": { "org_id": "...", "product_id": "..." },
  "body": { "name": "new name", "price": 1000 },
  "expect": { "status": 200 }
}
```

Body assertions support a `$.dot.path` form, e.g. `"$.cabys.code": "..."`.
Status can be a single int or a list (e.g. `[200, 404]`) for tests where either is acceptable.

## When to edit the engine

The engine (`_engine/`) is the small, reusable bit copied from the
`lambda-local-test` skill. Don't edit it for service-specific concerns — put
those in `run_local.py` or in test data. If you find yourself needing to
change `event_builder.py` for cross-app-be, update the skill upstream too so
other services benefit.
