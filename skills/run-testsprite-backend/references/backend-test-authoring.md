# TestSprite Backend Python Authoring

Use this reference to write executable TestSprite backend tests that survive the cloud sandbox, validate real API semantics, and fail for the right reason.

## Execution model

TestSprite backend code is a Python script executed from top to bottom. It is not a normal repository test process and must not depend on pytest discovery.

Vendor documentation for the TestSprite 0.4.0 backend runner names these available packages:

- Python standard library;
- `requests`;
- `pytest`;
- `numpy`;
- `scipy`; and
- dependencies bundled with those packages.

The vendor does not document the backend Python runtime version. Do not depend on a guessed version. Do not import application modules or arbitrary packages; test TypeScript, Python, Java, Go, or any other server through its HTTP interface.

The saved code limit is 350 KB. Prefer one focused behavior per file.

Whether TestSprite generated the Python in the Portal or an agent authored it through the CLI, review it as executable third-party test code before saving or running it. Generation does not prove that the target, auth, timeout, cleanup, or assertion matches the repository contract.

## Start from the installed scaffold

```bash
testsprite test scaffold --type backend --out /tmp/testsprite-health.py
```

The released 0.4.0 scaffold and implementation use an explicit `BASE_URL`. Generic `--target-url` does not rewrite backend Python, while bundled vendor skill guidance also mentions `TARGET_URL`. Because the official surfaces conflict, use an explicit reviewed URL, do not teach `TARGET_URL` as guaranteed, and verify the observed host from correlated result/failure evidence and application logs:

```python
BASE_URL = "https://replace-with-public-target.invalid"
```

Replace the placeholder before upload. To change environments, update saved code with optimistic versioning or keep separately named environment-specific tests. Do not expect `--target-url` to rewrite backend code.

## Required file shape

```python
import requests

BASE_URL = "https://staging.service.test"


def test_health_contract() -> None:
    response = requests.get(f"{BASE_URL}/health", timeout=(10, 30))
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    assert response.headers.get("content-type", "").startswith("application/json")
    body = response.json()
    assert body.get("status") == "ok"


test_health_contract()
```

The final call is load-bearing for backend execution. TestSprite runs the script top-to-bottom rather than relying on pytest discovery. This skill and its auditor require synchronous zero-argument `test_*` functions so execution remains statically provable; that narrower subset is safety policy, not a claim that the platform rejects every other Python shape.

Do not catch `AssertionError`, call `pytest.skip`, or convert exceptions into `print` output. A script that reaches module end after swallowing its only failure is a false pass.

Avoid relying on this shape:

```python
class TestHealth:
    def test_health(self):
        ...
```

Without explicit construction/calls, top-to-bottom execution does not run the method.

## Managed authentication

Configure auth on the TestSprite backend project. Vendor-shipped backend skill contracts include `__AUTH_HEADERS__`, `__AUTH_CREDENTIAL__`, and `__AUTH_TYPE__`. Bind managed headers to one approved HTTPS origin. Every managed-header request must match the allowed scheme, canonical host, and effective port, reject URL userinfo/query targets, and set `allow_redirects=False` unless redirects were separately authorized. Consume a copy of `__AUTH_HEADERS__` without logging it. Never access, print, serialize, or expose `__AUTH_CREDENTIAL__`; avoid exposing `__AUTH_TYPE__` unless a narrowly reviewed non-secret branch requires it:

```python
import requests

BASE_URL = "https://staging.service.test"
AUTH_HEADERS = dict(__AUTH_HEADERS__)


def test_current_user() -> None:
    response = requests.get(
        f"{BASE_URL}/v1/me",
        headers=AUTH_HEADERS,
        timeout=(10, 60),
        allow_redirects=False,
    )
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    body = response.json()
    assert isinstance(body.get("id"), str) and body["id"]


test_current_user()
```

Do not access or print `__AUTH_CREDENTIAL__`. Do not construct literal `Authorization`, `X-API-Key`, Basic, cookie, or Bearer values. If the endpoint needs an additional non-secret header, merge it:

```python
headers = {**__AUTH_HEADERS__, "Idempotency-Key": "testsprite-profile-read-v1"}
```

Never put user identifiers, live keys, or environment secrets in stable idempotency values.

## Timeouts and bounded diagnostics

This skill requires an explicit timeout on every request so live verification stays bounded. That is a safety and audit policy, not a vendor platform requirement. A tuple separates connection and response-read budgets:

```python
response = requests.post(
    f"{BASE_URL}/v1/jobs",
    headers=__AUTH_HEADERS__,
    json={"mode": "summary"},
    timeout=(10, 120),
    allow_redirects=False,
)
```

Match the read budget to the documented service behavior and outer edge timeout. A 300-second client timeout cannot rescue a platform that terminates requests at 100 seconds.

Assertion messages should identify the contract without dumping sensitive bodies:

```python
assert response.status_code == 201, (
    f"create failed: status={response.status_code}, "
    f"request_id={response.headers.get('x-request-id', 'missing')}"
)
```

Avoid `print(response.text)`, full headers, cookies, tokens, or request bodies. TestSprite already records request/response evidence; treat artifacts as sensitive.

Distinguish four independent clocks when diagnosing “timeout”:

| Clock | Controlled by |
|---|---|
| Connect/read budget | Python `requests` `timeout=` |
| CLI polling ceiling | `test run/rerun/wait --timeout` |
| Edge/gateway deadline | CDN, load balancer, Worker, ingress, or reverse proxy |
| Upstream/provider deadline | Application/provider client policy |

Increasing one does not extend the others. An HTTP 524 or equivalent edge response is application architecture/runtime evidence, not a reason to increase the CLI polling ceiling.

## JSON contract helper

Use explicit parsing and informative structural checks:

```python
def require_json_object(response: requests.Response) -> dict:
    content_type = response.headers.get("content-type", "")
    assert "application/json" in content_type, f"unexpected content-type: {content_type!r}"
    try:
        body = response.json()
    except ValueError as exc:
        raise AssertionError("response was not valid JSON") from exc
    assert isinstance(body, dict), f"expected object, got {type(body).__name__}"
    return body
```

Assert required relationships, not only keys:

```python
body = require_json_object(response)
assert isinstance(body.get("items"), list)
assert body.get("count") == len(body["items"])
assert all(isinstance(item.get("id"), str) and item["id"] for item in body["items"])
```

## Typed error example

```python
import requests

BASE_URL = "https://staging.service.test"


def test_missing_field_is_typed_400() -> None:
    response = requests.post(
        f"{BASE_URL}/v1/widgets",
        headers={**__AUTH_HEADERS__, "Content-Type": "application/json"},
        json={},
        timeout=(10, 60),
        allow_redirects=False,
    )
    assert response.status_code == 400, f"expected 400, got {response.status_code}"
    body = response.json()
    assert body.get("error", {}).get("type") == "validation_error"
    fields = body.get("error", {}).get("fields")
    assert isinstance(fields, list) and "name" in fields


test_missing_field_is_typed_400()
```

Do not make an unauthorized success acceptable by writing `assert status in {200, 400}`. One test should represent one contract outcome.

## URL and citation validation

Use the documented citation field first. A recursive collector is acceptable only when the public contract permits several metadata shapes.

```python
from urllib.parse import urlparse


def require_http_urls(values: list[str]) -> None:
    assert values, "expected at least one URL"
    for value in values:
        parsed = urlparse(value)
        assert parsed.scheme in {"http", "https"}, f"invalid scheme: {parsed.scheme!r}"
        assert parsed.netloc, "URL has no host"
        assert parsed.hostname not in {"localhost", "example.com"}


def collect_urls(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        found.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            found.extend(collect_urls(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(collect_urls(child))
    return found
```

Avoid letting an unrelated help/documentation URL satisfy a citation contract. Assert that the expected citation/source container exists before collecting its URLs.

For APIs that expose route metadata, validate it alongside sources instead of searching the whole body for convenient values:

```python
body = require_json_object(response)
sources = body.get("sources")
assert isinstance(sources, list), "missing documented sources array"
urls = [item["url"] for item in sources if isinstance(item, dict) and isinstance(item.get("url"), str)]
require_http_urls(urls)
meta = body.get("x_meta")
assert isinstance(meta, dict) and meta.get("routing") in {"primary", "secondary"}, "invalid routing metadata"
```

Replace the illustrative field names and route enum with the public contract. Never accept every route merely because another environment uses it.

## Defensive SSE example

```python
import json
import requests

BASE_URL = "https://staging.service.test"


def test_stream_contract() -> None:
    response = requests.post(
        f"{BASE_URL}/v1/stream",
        headers={**__AUTH_HEADERS__, "Accept": "text/event-stream"},
        json={"query": "stable test query", "stream": True},
        stream=True,
        timeout=(10, 150),
        allow_redirects=False,
    )
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    assert "text/event-stream" in response.headers.get("content-type", "")

    events: list[dict] = []
    done = False
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line or raw_line.startswith(":"):
            continue
        if not raw_line.startswith("data:"):
            continue
        data = raw_line.removeprefix("data:").strip()
        if data == "[DONE]":
            done = True
            break
        try:
            event = json.loads(data)
        except json.JSONDecodeError as exc:
            raise AssertionError("SSE data was not valid JSON") from exc
        assert isinstance(event, dict)
        events.append(event)

    assert done, "stream ended without terminal marker"
    assert events, "stream had no JSON events"
    assert not any(event.get("error") for event in events), "stream contained an error event"
    text = "".join(
        event.get("delta", "")
        for event in events
        if isinstance(event.get("delta"), str)
    )
    assert text.strip(), "stream contained no accumulated content"


test_stream_contract()
```

Adapt event fields and terminal semantics to the real API. Do not copy this parser unchanged when the endpoint uses event names, multiline `data:` blocks, OpenAI chunks, or NDJSON. Capture one sanitized real fixture and test the observed shape.

If sources or routing metadata can arrive in stream events, accumulate them from the documented event shapes and assert them after `[DONE]`. Keep a separate non-stream test: production systems often use different mapper and accumulator code, so one path can preserve citations while the other drops them.

## Stateful self-contained example

```python
import requests

BASE_URL = "https://replace-with-public-target.invalid"


def test_resource_lifecycle() -> None:
    created = requests.post(
        f"{BASE_URL}/v1/resources",
        headers=__AUTH_HEADERS__,
        json={"name": "testsprite-fixture"},
        timeout=(10, 60),
        allow_redirects=False,
    )
    assert created.status_code == 201
    resource_id = created.json()["id"]

    try:
        fetched = requests.get(
            f"{BASE_URL}/v1/resources/{resource_id}",
            headers=__AUTH_HEADERS__,
            timeout=(10, 60),
            allow_redirects=False,
        )
        assert fetched.status_code == 200
        assert fetched.json().get("id") == resource_id
    finally:
        deleted = requests.delete(
            f"{BASE_URL}/v1/resources/{resource_id}",
            headers=__AUTH_HEADERS__,
            timeout=(10, 60),
            allow_redirects=False,
        )
        assert deleted.status_code in {200, 204, 404}


test_resource_lifecycle()
```

Use a dedicated test tenant and a collision-resistant fixture name if parallel runs are possible. Cleanup must be idempotent.

## Assertion ledger

Before any run, freeze a ledger mapping each material contract and cleanup obligation to its exact saved-code `assert`, contract source, expected test ID, and graph role. Reject missing material assertions, unasserted cleanup, `pytest.skip`, swallowed assertions/exceptions, or assertions deleted, weakened, or widened after failure. After every `test code put`, export the final saved code and `codeVersion`, then reconcile the ledger against that exact version.

The auditor requires at least one reachable non-static assertion per called `test_*` and rejects obvious skip/swallowing patterns. It cannot prove assertion strength, semantic completeness, or cleanup coverage; an auditor pass never replaces the ledger.

## Local static audit

Resolve `TESTSPRITE_SKILL_DIR` to the directory containing the loaded `run-testsprite-backend/SKILL.md`. Run before every `test create` or `test code put`:

```bash
python3 "$TESTSPRITE_SKILL_DIR/scripts/audit_backend_test.py" \
  --allowed-origin "https://staging.service.example" \
  /tmp/testsprite-test.py
```

Use `--allowed-origin` whenever managed headers appear; it must be the exact approved HTTPS origin with no path/query/userinfo. Add `--auth-required` when the contract requires authenticated success. Omit `--auth-required` for public endpoints and negative authentication tests whose expected result is `401` or `403`.

Managed requests require explicit `allow_redirects=False`. The exceptional `--allow-managed-redirects` auditor flag is only for redirects separately named in the authorization gate; it does not itself grant authorization.

Use JSON in automation, preserving the same auth/origin flags:

```bash
python3 "$TESTSPRITE_SKILL_DIR/scripts/audit_backend_test.py" \
  --json --allowed-origin "https://staging.service.example" \
  /tmp/testsprite-test.py
```

Maintainers and CI may run `audit_backend_test.py --self-test` as a deterministic built-in checker for the auditor itself. It is not part of the ordinary local authoring workflow.

`--allow-module NAME` is an escape hatch only after current official runner documentation proves the module is installed and you inspect its definition-time behavior. It does not install anything in TestSprite, admit reflection/loader modules, or make a non-`requests` HTTP client auditable.

The auditor fails closed on branch-only HTTP calls because it cannot execute arbitrary test code safely. When dynamic branches choose equivalent request variants, choose the URL/payload in the branch and issue one shared request afterward. Keep early-return paths behind a request that already proved the intended API behavior.

The execution proof intentionally accepts a constrained subset rather than pretending to interpret arbitrary Python:

- each called `test_*` function issues its first HTTP request directly as a request expression, assignment, annotation assignment, return value, or inside one `with requests.Session()` block;
- that request appears before branches, loops, `try`, returns, helper calls, mutation, or other dynamic control flow;
- every request receiver and argument uses static data expressions, safe constructors, or previously bound values—not helper calls, mutators, process exits, or side-effecting Session constructor arguments;
- request values carried by a loop use a simple loop target over a non-empty static list, tuple, or set; nested loop variants are all audited and are limited to 64 combinations;
- each called `test_*` reaches at least one non-static `assert`; helper assertions count only when their call is on the audited unconditional path;
- HTTP calls stay in `test_*` functions; helpers parse and assert on responses after the first request;
- module scope contains only imports, static assignments, function definitions, and direct zero-argument `test_*()` calls;
- imports name every dependency explicitly and stay inside the auditor's data/parsing-oriented standard-library subset (`from module import *` is rejected); and
- nested definitions/classes, lambdas, generators, decorators, duplicate definitions, non-static defaults, runtime reflection/loaders, request monkey-patching, and unresolved or local/private target hosts are rejected.

This boundary is deliberate. Put the first create/read request before a `try/finally`, as in the stateful example, then use dynamic cleanup or parsing afterward. Compute safe dynamic values in plain assignments; if their construction needs a helper call, simplify or inline the request fixture so the preflight can prove evaluation reaches HTTP. Keep helper functions at module scope and give defaults only resolved static literals or module constants. Because the runner version is undocumented, use `from __future__ import annotations` before syntax whose runtime support you have not established; ordinary `requests.Response`, `list[str]`, and `dict` annotations are accepted by the auditor directly. Request modules, imported methods, Session constructors/instances, and their methods are immutable: do not alias, rebind, monkey-patch, pass them to helpers, capture them in defaults or class bases, or mutate Session state; use per-request arguments and a `with requests.Session()` block. Runtime reflection and dynamic imports (`globals`, `locals`, `vars`, `sys`, `runpy`, `__loader__`, `__import__`, or import helpers) are rejected except for the exact managed-header lookup. Treat managed header dictionaries as immutable independent copies: use `dict(__AUTH_HEADERS__)` or `{**__AUTH_HEADERS__, "Accept": "application/json"}`, never a simple alias, function default, or mutation with `clear`, `pop`, `update`, or item assignment. Timeouts must be positive finite literals (or a bound static name). Targets must expose a statically verifiable public HTTP(S) hostname plus authority boundary; managed-header targets must exactly match `--allowed-origin` by scheme/canonical host/effective port, contain no userinfo/query, and disable redirects unless separately authorized.

## Authoring checklist

- Public target is real and revision-verifiable.
- Every `test_*` function is called.
- Every execution path through a called test reaches at least one real HTTP request.
- Every HTTP call has a timeout.
- Imports fit the current sandbox.
- Managed-header requests match `--allowed-origin` exactly and disable redirects unless separately authorized.
- No credential-like literals appear in URL queries, `params`, `data`, or `json` mappings.
- No response/token/header dumps.
- Assertions cover status, shape, and semantics.
- Dynamic values use invariants.
- Generated code was reviewed against repository truth before upload.
- Streaming parser matches a real sanitized fixture.
- Normal and streaming source paths are tested separately when their mappers differ.
- Mutations have idempotent cleanup.
- File passes `audit_backend_test.py`.
- Test code is at most 350 KB.

## Troubleshooting authoring

| Symptom | Likely authoring cause | Fix |
|---|---|---|
| Instant pass with no request | Test is uncalled, conditionally called, or has a request-free path | Add a direct module-scope call and ensure each path makes a real request; audit again |
| Import error in cloud | Project/arbitrary package imported | Replace with HTTP and supported modules |
| Authenticated endpoint returns 401 | Managed headers unused or project credential stale | Consume `__AUTH_HEADERS__`; verify project auth |
| Run hangs | Missing/oversized timeout or stream terminal not handled | Bound connect/read timeout and terminal condition |
| HTTP 524 persists after increasing CLI timeout | Edge deadline terminates the request before TestSprite polling matters | Fix or redesign the deployed request path; keep clocks distinct |
| Citation test passes on wrong URL | Recursive collector saw unrelated URL | Assert citation container first |
| Non-stream sources pass but stream sources fail | Separate accumulator/parser lost metadata | Capture a real stream fixture and fix/test that path independently |
| SSE parser fails intermittently | Assumed chunk boundaries or wrong event shape | Parse protocol lines and use sanitized real fixture |
| Test leaks fixture | Cleanup only on happy path | Use `try/finally` or verified teardown |
