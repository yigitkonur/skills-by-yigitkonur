# TestSprite Backend Python Authoring

Use this reference to write executable TestSprite backend tests that survive the cloud sandbox, validate real API semantics, and fail for the right reason.

## Execution model

TestSprite backend code is a Python script executed from top to bottom. It is not a normal repository test process and must not depend on pytest discovery.

Current TestSprite 0.3.0 guidance documents:

- Python standard library;
- `requests`;
- `pytest`;
- `numpy`;
- `scipy`; and
- dependencies bundled with those packages.

Do not import application modules or arbitrary packages. Test TypeScript, Python, Java, Go, or any other server through its public HTTP interface.

The saved code limit is 350 KB. Prefer one focused behavior per file.

## Start from the installed scaffold

```bash
testsprite test scaffold --type backend --out /tmp/testsprite-health.py
```

The 0.3.0 scaffold uses an explicit `BASE_URL`. A 0.3.0 command-shape probe confirms that `--target-url` has no effect for backend tests even though older bundled agent guidance suggested a runner-provided variable. Use an explicit public URL and verify it in the completed run's Data Flow:

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

The final call is load-bearing. A defined-but-uncalled function can produce a vacuous pass because no assertion executed. Keep top-level test functions synchronous and zero-argument; TestSprite does not inject pytest fixtures into a direct call, and calling an `async def` without an event loop only creates an unexecuted coroutine.

Avoid relying on this shape:

```python
class TestHealth:
    def test_health(self):
        ...
```

Without explicit construction/calls, top-to-bottom execution does not run the method.

## Managed authentication

Configure auth on the TestSprite backend project. The runner prepends managed credential values, including `__AUTH_HEADERS__`. Consume the headers without logging or copying the underlying credential:

```python
import requests

BASE_URL = "https://staging.service.test"
AUTH_HEADERS = dict(__AUTH_HEADERS__)


def test_current_user() -> None:
    response = requests.get(
        f"{BASE_URL}/v1/me",
        headers=AUTH_HEADERS,
        timeout=(10, 60),
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

Every request needs an explicit timeout. A tuple separates connection and response-read budgets:

```python
response = requests.post(
    f"{BASE_URL}/v1/jobs",
    headers=__AUTH_HEADERS__,
    json={"mode": "summary"},
    timeout=(10, 120),
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

## Stateful self-contained example

```python
resource_id = None
try:
    created = requests.post(
        f"{BASE_URL}/v1/resources",
        headers=__AUTH_HEADERS__,
        json={"name": "testsprite-fixture"},
        timeout=(10, 60),
    )
    assert created.status_code == 201
    resource_id = created.json()["id"]

    fetched = requests.get(
        f"{BASE_URL}/v1/resources/{resource_id}",
        headers=__AUTH_HEADERS__,
        timeout=(10, 60),
    )
    assert fetched.status_code == 200
    assert fetched.json().get("id") == resource_id
finally:
    if resource_id is not None:
        deleted = requests.delete(
            f"{BASE_URL}/v1/resources/{resource_id}",
            headers=__AUTH_HEADERS__,
            timeout=(10, 60),
        )
        assert deleted.status_code in {200, 204, 404}
```

Use a dedicated test tenant and a collision-resistant fixture name if parallel runs are possible. Cleanup must be idempotent.

## Local static audit

Resolve `TESTSPRITE_SKILL_DIR` to the directory containing the loaded `run-testsprite-backend/SKILL.md`. Run before every `test create` or `test code put`:

```bash
python3 "$TESTSPRITE_SKILL_DIR/scripts/audit_backend_test.py" \
  --auth-required /tmp/testsprite-test.py
```

Use JSON in automation:

```bash
python3 "$TESTSPRITE_SKILL_DIR/scripts/audit_backend_test.py" \
  --auth-required --json /tmp/testsprite-test.py
```

`--allow-module NAME` is an escape hatch only after current official runner documentation proves the module is installed. It does not install anything in TestSprite.

The auditor fails closed on branch-only HTTP calls because it cannot execute arbitrary test code safely. When dynamic branches choose equivalent request variants, choose the URL/payload in the branch and issue one shared request afterward. Keep early-return paths behind a request that already proved the intended API behavior.

## Authoring checklist

- Public target is real and revision-verifiable.
- Every `test_*` function is called.
- Every execution path through a called test reaches at least one real HTTP request.
- Every HTTP call has a timeout.
- Imports fit the current sandbox.
- Managed headers supply authentication.
- No response/token/header dumps.
- Assertions cover status, shape, and semantics.
- Dynamic values use invariants.
- Streaming parser matches a real sanitized fixture.
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
| Citation test passes on wrong URL | Recursive collector saw unrelated URL | Assert citation container first |
| SSE parser fails intermittently | Assumed chunk boundaries or wrong event shape | Parse protocol lines and use sanitized real fixture |
| Test leaks fixture | Cleanup only on happy path | Use `try/finally` or verified teardown |
