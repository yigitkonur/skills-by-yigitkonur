---
name: run-testsprite-backend
description: Use if creating, debugging, or release-gating TestSprite backend API tests against real services.
---

# Run TestSprite Backend

Use TestSprite as an independent HTTP client against a publicly reachable deployment. Build executable Python tests from repository truth, run them through the TestSprite cloud, inspect immutable run evidence, fix the demonstrated layer, and repeat until a fresh run verifies the intended deployed revision.

This workflow is TypeScript-backend-first. For another stack, inspect and substitute that repository's route, schema, test, build, and deployment conventions; TestSprite still exercises the service over HTTP.

## Essential rules

1. Read the nearest repository instructions before touching code or TestSprite state.
2. Test a public deployment and prove which revision it serves. A green run against old code is not release proof.
3. Store API credentials in TestSprite. Never put secrets in saved test code, command arguments, logs, artifacts, or git.
4. Call every backend `test_*` function. TestSprite executes Python top-to-bottom; it does not rely on pytest discovery.
5. Use only Python stdlib plus the packages supported by the current backend sandbox. Exercise project code through HTTP, never by importing it.
6. Keep live tests bounded, deterministic, and reversible. Do not turn a verification suite into load, abuse, or destructive production testing.
7. Treat TestSprite's LLM analysis as a hypothesis. Accept a root cause only after artifacts, repository code, and runtime evidence agree.

## When to use this skill

Use it when the user asks to:

- bootstrap or deepen TestSprite backend/API coverage;
- turn OpenAPI and product rules into executable cloud tests;
- debug a failed TestSprite backend run or artifact;
- verify streaming, sources, headers, routing metadata, auth, or error contracts;
- rerun tests after a fix and prove the exact deployed revision; or
- add TestSprite backend verification to CI.

Do not use it for frontend browser plans, local unit tests alone, generic API-client implementation, load/security scanning, or a service with no publicly reachable test target. Use a frontend TestSprite workflow for browser journeys and the repository's native test framework for local tests.

## Reference router

Load only the references needed for the current phase. Every reference is self-contained enough to enter at that phase.

| Situation | Read |
|---|---|
| Unfamiliar repo, missing project mapping, or uncertain deployed revision | [references/repo-discovery.md](references/repo-discovery.md) |
| New suite, coverage gaps, dependencies, streaming, or production-safety design | [references/suite-design.md](references/suite-design.md) |
| Writing or auditing TestSprite Python | [references/backend-test-authoring.md](references/backend-test-authoring.md) |
| Exact 0.3.0 commands, flags, outputs, exit codes, or official sources | [references/cli-reference.md](references/cli-reference.md) |
| Failed, blocked, flaky, deferred, or contradictory results | [references/failure-loop.md](references/failure-loop.md) |
| Credentials, CI, artifacts, deployment proof, and final release gate | [references/release-security.md](references/release-security.md) |

Common reading sets:

- First suite: repo discovery + suite design + authoring + release/security.
- Existing-test verification: repo discovery + CLI reference + failure loop.
- Authenticated CI: CLI reference + release/security.
- Streaming/provider failure: authoring + failure loop + release/security.

## Workflow

### 1. Frame a concrete verification goal

Write down:

- behavior or contract to prove;
- public target environment;
- expected deployed revision;
- allowed mutations and cleanup path;
- relevant endpoints and authentication mode; and
- completion condition: a fresh TestSprite run, terminal verdict, and revision evidence.

Separate code correctness from environment availability. An account shortage, CAPTCHA, proxy failure, or upstream outage is not evidence that repository code is wrong; it is also not a pass.

### 2. Discover repository truth

Read repository instructions, package manifests, routes/controllers, OpenAPI or other schemas, product docs, native tests, live harnesses, deployment workflow, and version/health endpoints. For TypeScript, start with `package.json`, workspace config, route registrations, handlers, contract types, and `*.test.ts`. For another stack, inspect the equivalent surfaces.

Rank conflicting evidence:

1. observed behavior of the intended deployed revision;
2. executable server code and tests;
3. published API schema;
4. maintained product documentation;
5. old examples and generated prose.

Do not silently normalize contradictions. Record whether the implementation, schema, or deployment is stale. Follow [repo discovery](references/repo-discovery.md) for the full evidence brief.

### 3. Preflight the current CLI and account

Examples below were verified with TestSprite CLI 0.3.0. Put global flags before the subcommand and let the installed `--help` win when a newer version differs.

```bash
testsprite --version
testsprite --output json auth status
testsprite --output json doctor
testsprite --output json usage
```

Require 0.3.0 or newer for managed backend credentials. If the CLI is absent, follow the official installation path. If authentication fails, use `testsprite setup`; never work around it by embedding an API key in test code. `doctor` can expose connectivity, profile, scope, or stale agent-guidance failures; read its JSON rather than ignoring a nonzero exit.

### 4. Resolve the backend project and current suite

Resolve in this order:

1. an explicit project ID supplied for the task;
2. `TESTSPRITE_PROJECT_ID`;
3. a repository `.testsprite/config.json` with `projectId`; then
4. project-name matching from the API.

```bash
testsprite --output json project list --max-items 100
testsprite --output json project get "$PROJECT_ID"
testsprite --output json test list --project "$PROJECT_ID" --type backend --max-items 100
testsprite --output json test list --project "$PROJECT_ID" --type backend --status failed,blocked
```

Do not guess when several projects plausibly match. Compare project type, existing test names, repository docs, and recent run targets. A project is one type; create a backend project only if no correct one exists and the task authorizes external project creation.

### 5. Prove the target before spending a run

TestSprite calls a deployed URL; it does not deploy or host the application. Confirm that the target is public HTTP(S), healthy, and serving the intended revision using the repository's version endpoint, image label, deployment API, or exact-SHA CI evidence.

In TestSprite 0.3.0, backend tests define their base URL inside saved Python. The CLI accepts `--target-url` but prints an advisory that it has no effect for backend tests. Verify the saved code and completed run Data Flow point to the intended environment. To change environments, update the saved code optimistically or maintain clearly named environment-specific tests. If the revision cannot be proven, the run may diagnose the current deployment but cannot verify the change.

### 6. Configure authentication without exposing it

Use a secret file populated through an authorized secret manager or protected local path. Do not use `--credential <value>` in agent-driven workflows because arguments can leak through shell history and process listings.

```bash
testsprite --output json project credential "$PROJECT_ID" \
  --type "Bearer token" --credential-file "$CREDENTIAL_FILE"

testsprite --output json project credential "$PROJECT_ID" --type public
```

Use `project auto-auth` with its `*-file` flags for recurring tokens when the plan supports it. In Python, copy `__AUTH_HEADERS__` into each authenticated request; never print `__AUTH_CREDENTIAL__`. Read [release and security](references/release-security.md) before changing credentials or handling old tests that once contained secrets.

### 7. Design the suite before creating tests

Build a traceable matrix from documented behavior, not a pile of happy-path status checks. Cover, where applicable:

- health/version and one representative success per public capability;
- authentication and authorization failures;
- input validation and typed error bodies;
- response structure plus semantic invariants;
- headers, source URLs, routing or correlation metadata;
- streaming event order, terminal event, and accumulated result;
- idempotency or state transitions;
- external-provider failure typing; and
- cleanup for created fixtures.

Use stable assertions: types, allowed enums, required non-empty values, URL validity, event ordering, and relationships between fields. Avoid exact model prose, timestamps, generated IDs, latency, or provider wording unless the contract guarantees them. See [suite design](references/suite-design.md).

### 8. Author and audit executable Python

Start from the current local scaffold:

```bash
testsprite test scaffold --type backend --out /tmp/testsprite-health.py
```

Replace its placeholder URL and assertion. A minimal authenticated test looks like this:

```python
import requests

BASE_URL = "https://api.example.com"
AUTH_HEADERS = dict(__AUTH_HEADERS__)


def test_profile_contract() -> None:
    response = requests.get(
        f"{BASE_URL}/v1/profile",
        headers=AUTH_HEADERS,
        timeout=(10, 60),
    )
    assert response.status_code == 200, f"expected 200, got {response.status_code}"
    body = response.json()
    assert isinstance(body.get("id"), str) and body["id"]
    assert body.get("status") in {"active", "limited"}


test_profile_contract()
```

Replace the example URL with the real public target. `__AUTH_HEADERS__` is supplied by the configured TestSprite credential. Never leave `example.com` in created code, and do not expect `--target-url` to rewrite backend Python.

Resolve `TESTSPRITE_SKILL_DIR` to the directory containing this loaded `SKILL.md`, then run the bundled static auditor before upload. Do not assume the skill is installed inside the target repository.

```bash
python3 "$TESTSPRITE_SKILL_DIR/scripts/audit_backend_test.py" \
  --auth-required /tmp/testsprite-profile.py
```

It rejects syntax errors, uncalled tests, unsupported imports, missing request timeouts, private/placeholder targets, and likely embedded credentials without printing secret values. Read [backend authoring](references/backend-test-authoring.md) for JSON, SSE, URL, error, and stateful examples.

### 9. Preview shape, then create and run one narrow test

`--dry-run` validates command shape only. It does not execute Python, authenticate to the application, validate the deployed target, or consume a real run.

```bash
testsprite --dry-run --output json test create \
  --type backend --project "$PROJECT_ID" --name "profile contract" \
  --code-file /tmp/testsprite-profile.py --run --wait --timeout 600

testsprite --output json test create \
  --type backend --project "$PROJECT_ID" --name "profile contract" \
  --code-file /tmp/testsprite-profile.py --run --wait --timeout 600
```

Capture the returned project ID, test ID, run ID, target, status, `dashboardUrl`, and exit code. Exit 7 means the same run is still available: resume it with `test wait`; do not trigger a duplicate.

### 10. Diagnose failures from pinned evidence

For a failed, blocked, or cancelled run, download its immutable run-scoped bundle:

```bash
mkdir -p .testsprite/runs
testsprite --output json test artifact get "$RUN_ID" \
  --out ".testsprite/runs/$RUN_ID"
testsprite --output json test steps "$TEST_ID" --run-id "$RUN_ID" --max-items 100
testsprite --output json test result "$TEST_ID" --include-analysis
```

Classify the failure before editing anything: product code, test code, deployment/config, TestSprite runner/transport, external dependency, or dependency starvation. Verify the LLM hypothesis against request/response evidence and the repository path. Follow [the failure loop](references/failure-loop.md).

### 11. Fix the demonstrated layer and preserve the contract

- Product defect: add a native regression, fix the code, pass exact-SHA CI, deploy that SHA, and rerun.
- Test defect: edit only the incorrect setup/parser/assertion; do not weaken the product contract.
- Deployment defect: correct the target/config/revision and re-probe before rerunning.
- External dependency: record the provider evidence and retry only when the dependency is actually recoverable.
- Dependency starvation: fix the failed producer before judging consumers.

Update saved code with optimistic concurrency:

```bash
testsprite test code get "$TEST_ID" --out /tmp/testsprite-current.py
testsprite --output json test code get "$TEST_ID"
testsprite --output json test code put "$TEST_ID" \
  --code-file /tmp/testsprite-fixed.py --expected-version "$CODE_VERSION"
```

Do not use `--force` unless you have proved the competing edit is disposable.

### 12. Expand safely, then finish with a fresh run

Declare real producer/consumer/teardown relationships at create time with `--produces`, `--needs`, and `--category teardown`. Change that graph by deleting and recreating the affected tests; current read/update commands do not round-trip the graph.

Use `test run --all` only when the saved targets are correct and endpoint concurrency is safe. Its `--max-concurrency` bounds CLI dispatch/polling; it does not promise serialization inside the service. Run capacity-heavy, account-bound, or mutable tests individually when shared-state safety is unproven.

Use `test rerun` for a fast saved-code replay. Backend reruns execute the dependency closure, may consume credits, and do not auto-heal. Use `--skip-dependencies` only when the named test is genuinely self-contained. A rerun is not the final release gate.

After the fix is deployed, confirm the saved Python targets it, then run a **fresh** relevant test or safe batch against the intended revision:

```bash
testsprite --output json test run "$TEST_ID" \
  --wait --timeout 600

testsprite --output json test run --all --project "$PROJECT_ID" \
  --wait --timeout 600 --max-concurrency 4 \
  --report junit --report-file ./testsprite-junit.xml
```

Do not use the batch command when its fixed saved targets or concurrency are unsafe. Re-check the served revision after the run.

## Completion record

Report every remaining test separately; never collapse environmental failures into “code green.”

| Field | Required evidence |
|---|---|
| Project and test | Project ID/name and test ID/name |
| Target | Public base URL and environment |
| Revision | Expected SHA and observed deployed SHA |
| Run | Run ID, fresh/rerun, terminal status, exit code |
| Contract | Exact semantic behavior asserted |
| Failure | Classification, artifact path, and evidence if non-passing |
| Fix | Repository regression/commit or environment action |
| Final gate | Fresh run after deploy, or an explicit unpassed external gate |

Claim only the rung reached. “Native CI is green” and “TestSprite verified production” are different facts.

## Pitfalls

| Pitfall | Corrective action |
|---|---|
| Test function is defined but not called | Call it at module bottom; run the auditor |
| Test only checks HTTP 200 | Assert body shape and business/source/routing invariants |
| Key pasted into saved code | Move it to `project credential`; rotate if exposed |
| Run starts before deployment | Prove target revision first |
| Exit 7 triggers another run | Resume the same run with `test wait` |
| Latest failure is mistaken for a specific run | Download `artifact get <run-id>` |
| Consumer fails because producer failed | Triage the producer; label consumer as starved |
| Rerun is reported as release proof | Finish with a fresh `test run` after deploy |
| `--target-url` is assumed to retarget backend tests | Update saved Python or use environment-specific tests; verify Data Flow |
| LLM recommendation is applied directly | Reconcile artifact, runtime, and repository evidence |

## Trigger calibration

Should trigger:

- “Create a TestSprite backend suite from this OpenAPI file.”
- “Run the API tests against staging and debug the failures.”
- “Test our SSE endpoint and citation URLs with TestSprite.”
- “Move these TestSprite tests to managed credentials.”
- “Add TestSprite backend checks to CI and gate the deployed SHA.”
- “Why is this TestSprite consumer starved after the producer failed?”
- “Rerun the TestSprite API tests after deploying this fix.”

Should not trigger:

- “Write Vitest unit tests for this parser.”
- “Create a TestSprite frontend browser journey.”
- “Benchmark this endpoint at 5,000 requests per second.”
- “Implement an HTTP client SDK.”
- “Fuzz this API for security vulnerabilities.”
- “Validate OpenAPI formatting without calling a deployment.”
- “Mock the database in pytest.”
