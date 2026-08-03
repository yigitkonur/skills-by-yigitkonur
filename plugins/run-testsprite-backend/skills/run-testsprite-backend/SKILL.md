---
name: run-testsprite-backend
description: Use skill if you are creating, debugging, running, or managing credentials for TestSprite backend API tests against deployed services; not frontend, load, fuzz, security scanning, or native-only testing.
---

# Run TestSprite Backend

Use TestSprite as an independent HTTP client against a reviewed deployment. Build executable Python tests from repository truth, run them through TestSprite, correlate the returned evidence to one pinned run, fix the demonstrated layer, deploy the exact verified revision, and finish with a fresh external run.

This workflow is TypeScript-backend-first. For another stack, substitute that repository's route, schema, test, build, and deployment conventions; TestSprite still exercises the service over HTTP.

## Value boundary

TestSprite can expose defects that same-process tests miss and challenge semantic contracts such as citations, streaming order, routing metadata, typed failures, dependencies, and cleanup. It is not a deployment system, account/proxy provider, CAPTCHA solver, load tester, or autonomous maintainer. Its AI analysis is a hypothesis, not proof.

| TestSprite can establish | It cannot establish by itself |
|---|---|
| What the observed target returned to its client | That the target serves the checkout's commit |
| Whether saved assertions held for a pinned execution | That a suggested root cause is correct |
| Request, response, backend output, trace, and dependency evidence that the service returns | That every backend evidence surface is immutable or run-scoped |
| A fresh external pass after deployment | Native correctness, load tolerance, or security completeness |

## Essential rules

1. Read the nearest repository instructions before touching code or TestSprite state.
2. Prove the target revision. A green run against old or unknown code is not release proof.
3. Keep both credential planes out of code, arguments, logs, artifacts, and git.
4. Call every backend `test_*` function. Backend Python executes top-to-bottom; pytest discovery is not the execution model.
5. Use explicit reviewed `BASE_URL` values. Do not trust `--target-url` or `TARGET_URL` to retarget backend Python; verify the observed host.
6. Keep tests bounded, deterministic, and reversible. Timeouts and the auditor's synchronous zero-argument subset are this skill's safety policy, not TestSprite platform requirements.
7. Treat saved tests as durable contracts. Validate AI suggestions; refine and reuse rather than regenerate by default.
8. Freeze exact expected test IDs, graph closure, assertions, and cleanup obligations before any run. Never reclassify scope after a failure to manufacture green.
9. Require one fail-closed authorization record before any remote write, billable run, credential change, deployment, cancellation, or application side effect. Read-only discovery is the default.
10. Do not report a batch or rerun green until every expected member and dependency-closure result is terminal and passed.

## When to use this skill

Use it to bootstrap or deepen TestSprite backend coverage, turn API contracts into cloud tests, debug backend results, verify streaming/auth/metadata/error behavior, add deployed-revision CI checks, or prove a fix after deployment.

Do not use it for frontend browser plans, native unit tests alone, generic API-client implementation, load testing, fuzzing, security scanning, or destructive production probing. Hand frontend TestSprite journeys to the canonical `run-testsprite-frontend` skill. For a public target, the CLI workflow is sufficient and MCP is optional. For a localhost-only target, use TestSprite's documented MCP route; `testsprite agent install --target ...` installs local guidance and is not MCP.

Before spending runs, require a material consumer-visible contract, a deployed-boundary signal unavailable to native tests, or evidence for a meaningful external integration. A duplicate 200-only check has little value.

## Reference router

Load only the references needed for the current phase.

| Situation | Read |
|---|---|
| Unfamiliar repo, project conventions, MCP/public reachability, or uncertain deployed revision | [references/repo-discovery.md](references/repo-discovery.md) |
| New suite, coverage gaps, dependencies, streaming, or production-safety design | [references/suite-design.md](references/suite-design.md) |
| Writing or statically auditing TestSprite Python | [references/backend-test-authoring.md](references/backend-test-authoring.md) |
| Exact 0.4.0 commands, profiles, outputs, batch checks, cancellation, exit codes, or official sources | [references/cli-reference.md](references/cli-reference.md) |
| Failed, blocked, flaky, deferred, partial, or contradictory results | [references/failure-loop.md](references/failure-loop.md) |
| API keys, application credentials, CI, evidence handling, deployment proof, and final release gate | [references/release-security.md](references/release-security.md) |

Common reading sets:

- First suite: repo discovery + suite design + authoring + release/security.
- Existing-test verification: repo discovery + CLI reference + failure loop.
- Authenticated CI: CLI reference + release/security.
- Streaming/provider failure: authoring + failure loop + release/security.

## Workflow

### 1. Frame the verification goal

Record:

- behavior or contract to prove;
- target environment and expected deployed revision;
- allowed mutations and cleanup path;
- relevant endpoints and authentication mode;
- exact expected test IDs and producer/consumer/teardown closure, frozen before execution;
- assertion and cleanup obligations, frozen before execution; and
- completion condition: a fresh `test run`, terminal verdict, exact membership, and revision evidence.

Predeclare end states: `verified`, `product defect`, `test defect`, `deployment drift`, `runtime/provider gate`, or `TestSprite execution failure`. An account shortage, CAPTCHA, proxy failure, or upstream outage is not code evidence and is not a pass. Do not narrow, rename, or reclassify the frozen scope after a failure.

### 2. Establish the fail-closed authorization gate

Read-only repository and TestSprite discovery is the default. Before any remote write, billable run, credential operation, test create/update/code/metadata/cancel, deployment, or application side effect, require one explicit authorization record naming:

- TestSprite account/tenant, project ID, and exact test IDs;
- exact application target, environment, account/tenant, and credential environment;
- intended effect, including remote state and billable/provider side effects;
- maximum client polling concurrency and the separately bounded server/application concurrency plan;
- cleanup owner, exact cleanup operation, and success assertion; and
- rollback/recovery path for test state, credentials, deployment, and application data.

Fail closed if any field is absent or scope changes. The gate authorizes only the named operations and does not convert generated plans, a prior run, or general repository access into permission for writes or execution.

### 3. Discover repository truth

Read repository instructions, manifests, routes/controllers, schemas, product docs, native tests, live harnesses, deployment workflow, and version/health surfaces. Rank conflicting evidence:

1. observed behavior of the intended deployed revision;
2. executable server code and tests;
3. published API schema;
4. maintained product documentation;
5. old examples and generated prose.

Record contradictions instead of silently normalizing them. Follow [repository discovery](references/repo-discovery.md) for the evidence brief.

### 4. Install and preflight CLI 0.4.0 without persisting secrets

TestSprite CLI 0.4.0 requires Node `^20.19.0 || ^22.13.0 || >=24` and provides the `testsprite` binary:

```bash
npm install --global @testsprite/testsprite-cli@0.4.0
testsprite --version
testsprite --output json auth status
testsprite --output json doctor
```

Before any CLI call that could send a TestSprite key, reject an inherited `TESTSPRITE_API_URL` unless the authorization gate names that exact TLS endpoint and confirms the key/profile belongs to its credential environment. Treat explicit `--endpoint-url` the same way; it is a credential-routing control, not a harmless connectivity flag. Never disclose the inherited value while checking it.

Prefer `TESTSPRITE_API_KEY` inherited from the environment. It overrides a stored profile even when `--profile NAME` is explicit. Never auto-run `setup`, `setup --from-env`, create `.env`/`.envrc`, or replay a key into a profile. `setup --from-env` persists the environment key. If persistent credential setup is explicitly authorized, use the credential-only path:

```bash
testsprite setup --no-agent
```

To use a stored profile key, unset the inherited key for every invocation, pass the profile explicitly, and verify `auth status` identity and scopes before any write or run:

```bash
env -u TESTSPRITE_API_KEY testsprite --profile NAME --output json auth status
```

Released wrappers ignore `TESTSPRITE_PROFILE`. Global flags may appear in other accepted positions; this skill uses one consistent style without claiming the order is required.

Run `usage` only as an informational probe. Treat a balance as known only when balance fields are actually returned; Portal Billing is authoritative.

### 5. Resolve project and suite state

Use an explicitly supplied project ID first. `TESTSPRITE_PROJECT_ID` and `.testsprite/config.json` may be repository or skill conventions, but they are not general CLI defaults. Use them only when the repository documents them; otherwise resolve an unambiguous project from the API.

```bash
testsprite --output json project list --max-items 100
testsprite --output json project get "$PROJECT_ID"
testsprite --output json test list --project "$PROJECT_ID" --type backend --max-items 100
testsprite --output json test list --project "$PROJECT_ID" --type backend --status failed,blocked
```

Compare project type, names, saved code, recent targets, and repository docs. Create a backend project only when no correct project exists and external creation is authorized.

### 6. Prove the backend target

The released 0.4.0 implementation and scaffold use explicit code `BASE_URL`; `--target-url` does not reliably retarget backend code. Bundled vendor guidance also mentions `TARGET_URL`, so the official surfaces conflict. Use an explicit reviewed public `BASE_URL`, distrust overrides, and verify the observed target from result/failure evidence and application logs.

Capture before and after execution:

- base URL, environment, lane/tenant, and revision or image digest;
- TestSprite test ID and saved code version;
- application request ID and timestamps when available.

Matching pre/post revision strings are necessary but insufficient on a mutable target: traffic may have observed A→B→A between probes. Final proof requires an immutable revision URL/release, or request-correlated application and deployment evidence showing that the pinned TestSprite requests reached the intended revision and excluding mid-run drift.

If the service is localhost-only, route to the documented TestSprite MCP workflow rather than pretending the cloud CLI can reach it. Native `agent install` remains local guidance only.

### 7. Configure application authentication safely

The TestSprite API key authenticates the CLI. The TestSprite project credential authenticates backend Python to the application. Do not mix them.

Use protected credential files for project auth; avoid inline secret flags:

```bash
testsprite --output json project credential "$PROJECT_ID" \
  --type "Bearer token" --credential-file "$CREDENTIAL_FILE"

testsprite --output json project credential "$PROJECT_ID" --type public
```

Vendor-shipped backend contracts include `__AUTH_HEADERS__`, `__AUTH_CREDENTIAL__`, and `__AUTH_TYPE__`. Bind managed headers to one explicitly approved origin: exact scheme, canonical host, and effective port. Managed requests must use `allow_redirects=False` unless the authorization gate separately approves redirects, and must not place credentials in URL userinfo or query targets. Copy `__AUTH_HEADERS__` into authenticated requests. Never access, print, serialize, or expose `__AUTH_CREDENTIAL__`; do not needlessly expose `__AUTH_TYPE__`. Read [release and security](references/release-security.md) before changing credentials or handling historical leaks.

### 8. Design the suite

Build a traceable matrix from repository contracts. Cover relevant health/version, auth failures, validation, semantic success, headers/metadata, streaming order, state transitions, provider failure typing, and cleanup. Use stable invariants rather than exact model prose, timestamps, generated IDs, latency, or provider wording unless guaranteed.

Name the independent deployed-boundary signal each scenario adds. Keep non-streaming and streaming cases separate when their mapping paths differ. See [suite design](references/suite-design.md).

### 9. Author and audit executable Python

Start from the local scaffold in an unpredictable restricted directory:

```bash
umask 077
TESTSPRITE_WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/testsprite-backend.XXXXXXXX")"
testsprite test scaffold --type backend --out "$TESTSPRITE_WORK_DIR/profile.py"
```

Replace its target and assertions. The runner supports Python stdlib plus vendor-documented `requests`, `pytest`, `numpy`, and `scipy`; the Python runtime version is undocumented. Use explicit top-to-bottom calls:

```python
import requests

BASE_URL = "https://api.example.com"
AUTH_HEADERS = dict(__AUTH_HEADERS__)


def test_profile_contract() -> None:
    response = requests.get(
        f"{BASE_URL}/v1/profile",
        headers=AUTH_HEADERS,
        timeout=(10, 60),
        allow_redirects=False,
    )
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    body = response.json()
    assert isinstance(body.get("id"), str) and body["id"]
    assert body.get("status") in {"active", "limited"}


test_profile_contract()
```

Replace the example URL before upload. Before upload, create an assertion ledger. Map every material contract and cleanup obligation to the exact saved-code `assert` expression, its contract source, and expected test ID. Reject a test with no material assertion, unasserted cleanup, `pytest.skip`, swallowed assertion/exception paths, or an assertion deleted, weakened, or widened after failure. Freeze this ledger before execution; an auditor pass is not assertion proof.

Resolve `TESTSPRITE_SKILL_DIR` to this loaded skill directory and run its conservative static policy check. Authenticated audits require the exact approved HTTPS origin:

```bash
python3 "$TESTSPRITE_SKILL_DIR/scripts/audit_backend_test.py" \
  --auth-required --allowed-origin "https://api.example.com" \
  "$TESTSPRITE_WORK_DIR/profile.py"
```

The auditor rejects syntax errors, uncalled/request-free tests, tests without a reachable non-static `assert`, imports outside its allowlist, missing bounded request timeouts, private/placeholder targets, unsafe dynamic shapes, obvious skip/exception swallowing, likely embedded credentials, and managed-header origin/redirect violations without printing secret values. It intentionally accepts a narrower synchronous zero-argument subset than the platform may support. It cannot prove assertion strength or cleanup coverage; preserve and manually reconcile the assertion ledger. Read [backend authoring](references/backend-test-authoring.md).

### 10. Preview, then create and run one narrow test

`--dry-run` validates command shape only; it does not execute Python or prove auth, target, deployment, or behavior.

```bash
testsprite --dry-run --output json test create \
  --type backend --project "$PROJECT_ID" --name "profile contract" \
  --code-file "$TESTSPRITE_WORK_DIR/profile.py" --run --wait --timeout 600

testsprite --output json test create \
  --type backend --project "$PROJECT_ID" --name "profile contract" \
  --code-file "$TESTSPRITE_WORK_DIR/profile.py" --run --wait --timeout 600
```

For chained `test create --run --wait`, parse the nested 0.4.0 JSON fields: `.testId`, `.codeVersion`, `.run.runId`, and `.run.status`. Do not look for run fields at the top level. Capture those fields, observed target, timestamps, dashboard URL, and exit code. Exit 7 covers timeout, unsupported operation, and deferred cases; call `test wait` only when output contains a real run ID. Never invent or infer one.

### 11. Diagnose pinned evidence honestly

For backend failures, the released surfaces conflict: shipped code points to latest `test failure get TEST_ID`, while public docs advertise `test artifact get RUN_ID`. Do not promise immutable backend artifacts. Capture result/step/code/trace/artifact material only under `umask 077` in an unpredictable restricted directory; do not print raw application payloads into the transcript. Share only allowlisted correlation metadata and sanitized content.

Attempt the documented/run-oriented surface when supported, but correlate every retrieved result, failure bundle, `apiOutput`, and `trace` to the pinned run ID, code version, target, request IDs, and timestamps. If backend wait uses a legacy/test-level fallback, final proof additionally requires `runIdIfAvailable == RUN_ID`. Missing, null, mismatched, or unparseable run correlation is diagnostic only and must be classified as unresolved `TestSprite execution failure`, never a pass.

```bash
umask 077
TESTSPRITE_EVIDENCE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/testsprite-evidence.XXXXXXXX")"
testsprite --output json test steps "$TEST_ID" --run-id "$RUN_ID" --max-items 100 \
  > "$TESTSPRITE_EVIDENCE_DIR/steps.json"
testsprite --output json test result "$TEST_ID" --include-analysis \
  > "$TESTSPRITE_EVIDENCE_DIR/result.json"
testsprite --output json test failure get "$TEST_ID" \
  --out "$TESTSPRITE_EVIDENCE_DIR/failure"
```

Use `test artifact get "$RUN_ID"` only when installed help and actual backend output support it; do not silently substitute latest failure data for the pinned run. Classify product code, test code, deployment, configuration, auth/capacity, edge, provider, TestSprite runner, dependency starvation, or nondeterminism before editing. Follow [failure loop](references/failure-loop.md).

### 12. Fix the demonstrated layer

- Product defect: add a native regression, fix code, pass exact-revision CI, deploy that artifact, and rerun.
- Test defect: correct target/setup/parser/assertion without weakening the contract.
- Deployment defect: correct target/config/revision and prove it live before rerunning.
- Runtime/provider gate: preserve evidence and retry only after observable resource state changes.
- TestSprite defect: preserve run/request IDs and bounded diagnostics; do not patch product code without a faithful response.
- Dependency starvation: fix failed producers/teardowns before judging consumers.

Update code optimistically:

```bash
testsprite test code get "$TEST_ID" --out "$TESTSPRITE_WORK_DIR/current.py"
testsprite --output json test code get "$TEST_ID" \
  > "$TESTSPRITE_WORK_DIR/current-code.json"
testsprite --output json test code put "$TEST_ID" \
  --code-file "$TESTSPRITE_WORK_DIR/fixed.py" --expected-version "$CODE_VERSION"
```

After any code or metadata update, export the final saved code again, record the returned final `codeVersion`, and reconcile every ledger assertion and cleanup obligation against that exact version before another run. Do not accept deleted, weakened, widened, skipped, or exception-swallowed assertions.

TestSprite 0.4.0 also permits dependency metadata changes through `test update`, including `--produces`, `--needs`, and `--category`; inspect `testsprite test update --help`, review the current graph, and update in place instead of delete/recreate. Do not use forceful overwrites unless a competing edit is proven disposable.

### 13. Expand safely and prove exact outcomes

For batch execution, use the exact test IDs and graph closure frozen before any run. Exit 0 is insufficient: require no `conflicts`, deferred members, or skipped arrays; require returned membership to equal the expected set; and require every accepted member to be terminal `passed`. Missing, extra, queued, blocked, cancelled, or unknown members keep the batch non-green. Never drop a failed member or reclassify the closure after execution.

For backend `test run --all --wait`, `--max-concurrency` limits client polling only. It does not limit server execution, traffic, dispatch, shared-state overlap, or provider pressure; serialize or wave-order server work explicitly.

Backend rerun may execute a producer/teardown closure while the process exit reflects only the selected test. Inspect `closureFailures[]` and every closure member; any failed producer or teardown keeps the rerun non-green. `--skip-dependencies` is valid only for a truly self-contained test. Rerun and flaky checks are feedback, never final release proof.

Ctrl-C detaches local polling. Stop server-side execution explicitly when authorized:

```bash
testsprite --output json test cancel "$RUN_ID"
```

`test cancel` exits 0 when the run is cancelled or already cancelled, 4 when not found, 6 when the run is already terminal and cancellation conflicts, and may return 1 for a multi-error outcome. A subsequent `test wait` on a cancelled run exits 1. Cancellation does not refund credits; query and record final server state. Exit 14 is `CLIENT_TOO_OLD` and is never cancellation.

After deploying the exact verified revision and confirming the saved semantic contract and target are unchanged, finish with a fresh run:

```bash
testsprite --output json test run "$TEST_ID" --wait --timeout 600
```

An individual fresh run is final proof only for a self-contained test with no dependency or teardown relationship. Graph-backed release proof requires one fresh wave-ordered batch whose frozen membership is the exact producer/consumer/teardown closure and whose every member is terminal `passed` with no conflict, deferred, skipped, missing, or extra member.

Dry-run, rerun, flaky, queued, deferred, auto-attached, stale-target, or uncorrelated legacy fallback activity is not final proof. Re-probe the deployed revision after the run, exclude mutable-target A→B→A drift with immutable or request-correlated deployment evidence, and recheck the final saved code version against the assertion ledger.

## Completion record

Report each planned test separately; never collapse environmental or partial states into “code green.”

| Field | Required evidence |
|---|---|
| Project/test | Project ID/name and exact expected test IDs |
| Target | Explicit saved base URL, observed host, environment/lane |
| Revision | Expected SHA plus immutable release URL or request-correlated deploy/app proof excluding A→B→A drift |
| Run | Run ID, fresh/rerun, terminal status, exit code; legacy fallback `runIdIfAvailable` equality |
| Membership | Frozen exact set; no conflicts/deferred/skips; all terminal passed |
| Closure | Frozen producer/consumer/teardown wave and `closureFailures[]` |
| Test code | Final saved code version and assertion-ledger reconciliation |
| Assertions | Every material contract and cleanup obligation mapped to exact saved-code assertions |
| Evidence | Correlation basis; unresolved `TestSprite execution failure` if run scope is missing/unparseable |
| Fix | Native regression/commit or environment action |
| Final gate | Fresh run after deploy, or explicit unpassed external gate |

Claim only the rung reached. “Native CI is green” and “TestSprite verified the deployed contract” are different facts.

## Pitfalls

| Pitfall | Corrective action |
|---|---|
| API key is persisted automatically | Prefer inherited `TESTSPRITE_API_KEY`; never auto-run setup or create env files |
| `TESTSPRITE_PROFILE` is assumed active | Pass explicit `--profile`; unset `TESTSPRITE_API_KEY`, then verify identity/scopes |
| Endpoint override is inherited casually | Reject `TESTSPRITE_API_URL`/`--endpoint-url` unless exact TLS credential routing is authorized |
| Auditor pass is called assertion proof | Keep the assertion ledger; reject missing/weakened/widened assertions and unasserted cleanup |
| Test function is defined but not called | Call it at module bottom; run the auditor |
| Backend target override is trusted | Review explicit `BASE_URL`; verify observed host and revision |
| Latest failure is treated as pinned evidence | Correlate run/code/target/timestamps or report unresolved |
| Exit 7 always triggers wait | Wait only when output contains a real run ID |
| Batch exit 0 is called green | Check exact IDs, conflicts, deferred/skipped arrays, and terminal statuses |
| Selected rerun passed but producer failed | Inspect all closure members and `closureFailures[]` |
| Ctrl-C is treated as cancellation | Use authorized `test cancel RUN_ID`; parse 0/4/6/1 and remember later wait exits 1 |
| Exit 14 is treated as cancellation | Exit 14 is `CLIENT_TOO_OLD`; upgrade the client |
| Rerun is reported as release proof | Finish with a fresh `test run` after exact-revision deploy |
| LLM recommendation is applied directly | Reconcile TestSprite, runtime, repository, and deployment evidence |

## Trigger calibration

Should trigger:

- “Create a TestSprite backend suite from this OpenAPI file.”
- “Run the API tests against staging and debug the failures.”
- “Test our SSE endpoint and citation URLs with TestSprite.”
- “Move these TestSprite tests to managed credentials.”
- “Add TestSprite backend checks to CI and gate the deployed SHA.”
- “Why did this TestSprite batch exit zero with skipped tests?”
- “Cancel this TestSprite backend run on the server.”
- “Did this API suite find a regression or only an environment gate?”

Should not trigger:

- “Write Vitest unit tests for this parser.”
- “Create a TestSprite frontend browser journey.”
- “Benchmark this endpoint at 5,000 requests per second.”
- “Implement an HTTP client SDK.”
- “Fuzz this API for security vulnerabilities.”
- “Validate OpenAPI formatting without calling a deployment.”
- “Mock the database in pytest.”
