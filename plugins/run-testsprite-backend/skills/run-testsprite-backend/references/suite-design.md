# Backend Suite Design

Use this reference to turn API and product contracts into a broad but production-safe TestSprite backend suite with strong observable assertions.

## Design principle

Test from the consumer boundary. A useful backend test proves more than transport success:

```text
request accepted -> correct path executed -> response contract preserved -> semantic outcome true
```

HTTP 200 alone proves only that something answered.

Before adding a scenario, state its independent failure value: which consumer-visible regression could pass native tests yet fail through the deployed HTTP boundary? Keep representative, contract-dense tests; omit duplicate status-only coverage.

## 1. Build a coverage matrix

Start with capabilities, not endpoints. One endpoint may carry several materially different contracts; several endpoints may form one user outcome.

| Dimension | Typical cases | What to assert |
|---|---|---|
| Availability | health, version | status, content type, deployed revision |
| Authentication | missing, malformed, valid, insufficient scope | status, typed error, no data leak |
| Validation | missing field, wrong type, boundary, unknown enum | status and field-level error |
| Success | representative request per capability | structure and semantic invariants |
| Error mapping | not found, conflict, rate limit, upstream failure | stable error type, retry metadata |
| Metadata | source URLs, routing, correlation, pagination | presence, validity, consistency |
| Streaming | headers, first event, chunks, terminal event | order, parseability, accumulated result |
| State | create/read/update/delete | IDs and transitions round-trip |
| Idempotency | repeated key/request | no duplicate side effect |
| External provider | unavailable account, CAPTCHA, timeout | correct classification, no false success |

For a first TestSprite project, seed a broad suite across the main public capabilities. Do not report setup complete after one health test. For an existing project, add only gaps relevant to the change or stale contract.

Generated plans are a draft. Review each row for contract authority, target safety, stable data, expected cost, and whether TestSprite can execute it faithfully before generating or saving code.

## 2. Prioritize by failure value

Use stable prefixes in test names so filters are useful:

```text
P0 contract - unauthenticated request is typed 401
P0 semantic - search returns at least one valid source URL
P0 stream - terminal event follows content
P1 validation - unknown enum is typed 400
P1 integration - created item round-trips and is deleted
P2 external - provider timeout maps to retryable error
```

Suggested priority:

- **P0:** public contract, auth boundary, money/data-loss risk, core success, required source/routing guarantees.
- **P1:** important negative cases, state transitions, streaming order, idempotency.
- **P2:** rare provider conditions and expensive variants.
- **P3:** exploratory or diagnostic coverage that should not gate every release.

Use the CLI `--priority p0|p1|p2|p3` when creating tests, but keep the name meaningful without metadata.

## 3. Write observable semantic assertions

Strong assertions combine layers:

```python
assert response.status_code == 200
assert response.headers.get("content-type", "").startswith("application/json")
body = response.json()
assert isinstance(body.get("items"), list) and body["items"]
assert all(isinstance(item.get("id"), str) and item["id"] for item in body["items"])
assert body.get("routing") in {"primary", "secondary"}
```

Weak assertions:

```python
assert response.ok
assert "answer" in response.text
assert len(response.text) > 0
```

The weak version can pass on an error envelope, placeholder answer, or wrong route.

### Stable vs unstable values

| Assert directly | Assert by shape/invariant | Usually avoid |
|---|---|---|
| documented enum, error code, required header | generated ID is non-empty and reusable | exact generated ID |
| relationship between request and response | timestamp parses and is recent enough | exact timestamp |
| URL uses HTTP(S) and has a host | model text is non-empty and relevant enough for contract | exact model prose |
| terminal event appears after content | latency stays below a separately authorized SLO | provider latency in ordinary contract test |

## 4. Validate real source URLs

If the product promises sources/citations, assert usable URLs, not merely a `sources` key:

```python
from urllib.parse import urlparse


def assert_real_urls(values: list[str]) -> None:
    assert values, "expected at least one source URL"
    for value in values:
        parsed = urlparse(value)
        assert parsed.scheme in {"http", "https"}
        assert parsed.netloc
        assert parsed.hostname not in {"localhost", "example.com"}
```

Extract from the documented response shape first. Use a recursive URL collector only when the contract intentionally allows several citation shapes, and still assert the expected containing field or event so unrelated URLs cannot satisfy the test.

When normal and streaming responses use different parser/accumulator paths, keep separate source-contract tests:

| Mode | Minimum semantic proof |
|---|---|
| Non-streaming | non-empty answer, expected source container, valid real source URLs, required route metadata |
| Streaming | parseable events, correct order, accumulated answer, terminal marker, sources retained in the documented event/final metadata shape |

A non-streaming pass does not prove the stream accumulator, and a stream pass does not prove the ordinary response mapper.

## 5. Design streaming tests as protocols

For SSE or newline-delimited output, assert:

1. response status and streaming content type;
2. every relevant line/event parses;
3. required metadata appears in the allowed phase;
4. content accumulates to a non-empty result;
5. required source/routing fields are present;
6. terminal event appears exactly as the contract defines; and
7. no typed error event is silently treated as content.

Do not assert an exact number of chunks unless the protocol guarantees it. Networks and upstream providers can split equivalent content differently.

Example event ledger:

```python
events: list[dict] = []
for line in response.iter_lines(decode_unicode=True):
    if not line or not line.startswith("data:"):
        continue
    payload = line.removeprefix("data:").strip()
    if payload == "[DONE]":
        events.append({"kind": "done"})
        continue
    events.append(json.loads(payload))

assert events and events[-1].get("kind") == "done"
```

See [backend-test-authoring.md](backend-test-authoring.md) for a complete defensive SSE example.

## 6. Cover negative paths without abuse

Useful safe negatives:

- omit a required field;
- send an invalid enum or wrong JSON type;
- omit authentication;
- use a fixture identifier guaranteed not to exist;
- repeat an idempotent request with the same key;
- request a documented unsupported media type; and
- exceed a tiny documented boundary using one request.

Do not use TestSprite to brute-force authentication, enumerate other tenants, flood rate limits, submit exploit payload corpora, or induce expensive provider failures. Those require a separately authorized security/load methodology.

Portal-generated plans may suggest boundary/load/security categories. Selection in a generated plan is not authorization to run them against production. Replace high-volume cases with one bounded contract probe or move them to the appropriate specialist environment.

## 7. Model state and cleanup

Prefer a self-contained test when setup, assertion, and cleanup fit safely in one Python file:

```python
created_id = None
try:
    created = requests.post(..., timeout=(10, 60))
    created_id = created.json()["id"]
    fetched = requests.get(..., timeout=(10, 60))
    assert fetched.json()["id"] == created_id
finally:
    if created_id:
        cleanup = requests.delete(..., timeout=(10, 60))
        assert cleanup.status_code in {200, 204, 404}
```

Split into TestSprite producer/consumer/teardown tests only when the platform's captured Data Flow genuinely needs to cross test boundaries. Declare at create time:

```bash
testsprite --output json test create --type backend --project "$PROJECT_ID" \
  --name "fixture producer" --code-file /tmp/create.py --produces resource_id

testsprite --output json test create --type backend --project "$PROJECT_ID" \
  --name "fixture consumer" --code-file /tmp/read.py --needs resource_id

testsprite --output json test create --type backend --project "$PROJECT_ID" \
  --name "fixture cleanup" --code-file /tmp/delete.py --category teardown
```

The flags order waves; they do not make an unsafe cleanup correct. Verify captured variable names in TestSprite Data Flow. Dependency metadata is create-only in CLI 0.3.0; maintain a local ledger because list/get do not round-trip it.

## 8. Design for constrained external providers

Account-backed AI APIs, payment sandboxes, email providers, browser pools, and other scarce systems need explicit capacity rules:

| Risk | Design response |
|---|---|
| One account or slot per request | Run IDs serially; do not assume batch polling cap serializes service work |
| CAPTCHA/proxy/provider outage | Assert typed failure; classify environment separately from code |
| Long-running request | Use explicit connect/read timeouts matched to supported edge limits |
| Rate limit | Avoid retries inside the test unless contract requires one bounded retry |
| Billable call | Put in a filtered P1/P2 group and check credits before full runs |
| Non-deterministic model output | Assert structure, sources, routing, and non-empty semantics, not exact prose |

Three retries in product code do not justify three retries in the test. The test should observe the product's final contract, not multiply side effects.

Tag resource-dependent tests in their names/descriptions and keep their prerequisites visible:

```text
P0 deterministic - auth rejection is typed 401
P1 external - credential-backed success returns sources
P2 browser - proxy-backed route returns typed metadata
```

Only deterministic tests should become unconditional release gates unless the organization deliberately provisions and monitors the required external capacity.

## 9. Define pass, block, and cleanup outcomes

For each scenario, predeclare:

```text
pass: exact observable contract
product failure: response proves implementation defect
test failure: parser/setup/assertion does not represent contract
environment block: target/account/proxy/provider unavailable
runner failure: TestSprite transport/sandbox could not execute faithfully
cleanup: operation and idempotent accepted statuses
```

This prevents an LLM suggestion or convenient assertion edit from redefining success after a failure.

Do not average unlike outcomes into one “mostly green” verdict. Report deterministic product failures, stale-deployment failures, dependency-blocked consumers, and runtime/provider gates separately; each has a different owner and remediation.

## Suite review checklist

- Every main capability has at least one real success assertion.
- Every auth boundary has a negative test.
- Error tests assert typed bodies, not only status.
- Dynamic values are tested by invariant.
- Streaming tests assert order and terminal state.
- Source/routing promises are semantically validated.
- Mutations are isolated and cleaned up.
- Dependency graphs reflect real captured data.
- Expensive/shared-capacity tests are safely scheduled.
- Every test has a product-contract source and a failure classification.
- Every test adds a distinct deployed-boundary signal over native coverage.
- Normal and streaming response paths are covered separately when their mappers differ.
- Resource-dependent cases declare prerequisites and are not unconditional gates by accident.

## Troubleshooting design

| Symptom | Design fix |
|---|---|
| Many 200-only tests | Add semantic assertions tied to product rules |
| Flaky model text | Assert stable structure/sources/routing, not wording |
| Consumer intermittently has no ID | Fix producer capture/Data Flow; do not retry consumer alone |
| Cleanup leaves fixtures | Move cleanup into `finally` or a verified teardown wave |
| Full batch exhausts provider slots | Filter and serialize capacity-heavy test IDs |
| Negative test trips abuse controls | Replace with one bounded documented invalid case |
| Generated suite is broad but low-signal | Keep scenarios tied to material contracts; remove duplicate 200-only cases |
| Several tests fail for different layers | Report each classification; do not collapse them into one pass-rate diagnosis |
