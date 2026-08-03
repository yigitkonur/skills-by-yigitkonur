# TestSprite CLI Backend Reference (verified for 0.4.0)

Use this reference for backend-oriented TestSprite CLI 0.4.0 installation, commands, output checks, cancellation, exit handling, and official-source conflicts.

The released implementation, installed help, public docs, and bundled vendor skill do not agree on every backend behavior. For syntax, use installed `--help`; for observed behavior, use a bounded command or pinned run; for policy, follow this skill's stricter safety gates. Record conflicts instead of blending them.

Read-only discovery is the default. Before any remote write, billable run, credential operation, test create/update/code/metadata/cancel, deployment, or application side effect, require the fail-closed authorization record from [release-security.md](release-security.md): account/tenant, project/test IDs, exact target, effect, concurrency, cleanup assertion, and rollback.

## Installation and runtime

Package and binary:

```bash
npm install --global @testsprite/testsprite-cli@0.4.0
testsprite --version
testsprite --help
testsprite test run --help
```

CLI 0.4.0 requires Node `^20.19.0 || ^22.13.0 || >=24`. Pin the package in automation so a new release cannot silently change commands or output.

This reference uses the canonical style `testsprite --output json SUBCOMMAND`. Global flags need not precede subcommands; the style is consistency, not a parser requirement.

Core global flags:

| Flag | Purpose |
|---|---|
| `--output text|json` | Human or machine-readable output |
| `--profile NAME` | Select a persisted credential profile for this invocation |
| `--endpoint-url URL` | Credential-routing override; reject unless exact TLS endpoint and credential environment are authorized |
| `--request-timeout SECONDS` | Bound each CLI API request |
| `--verbose` / `--debug` | Diagnostics; inspect and redact before sharing |
| `--dry-run` | Preview client request shape without proving remote behavior |

Parse named JSON fields and tolerate additive unknown fields. Never treat an uninspected exit code as the whole verdict.

## API-key preflight without persistence

Before the first authenticated CLI call, fail closed if `TESTSPRITE_API_URL` is inherited unless the authorization record names that exact TLS TestSprite endpoint and confirms the selected key/profile belongs to the matching credential environment. Treat explicit `--endpoint-url` identically. Check presence without printing the value.

Prefer `TESTSPRITE_API_KEY` inherited from the environment:

```bash
testsprite --output json auth status
testsprite --output json doctor
```

Do not automatically:

- run `testsprite setup`;
- run `testsprite setup --from-env`;
- write `.env` or `.envrc`;
- print, replay, or place the key in arguments; or
- persist a profile merely because authentication is missing.

`setup --from-env` persists the environment key. If the user explicitly authorizes persistent credential setup, use the credential-only path and enter the key through its protected interactive flow:

```bash
testsprite setup --no-agent
```

Released command wrappers ignore `TESTSPRITE_PROFILE`. An inherited `TESTSPRITE_API_KEY` overrides a stored profile even when `--profile NAME` is explicit. To use the profile's key, unset the inherited key on every invocation and verify `auth status` identity and scopes before any write or run:

```bash
env -u TESTSPRITE_API_KEY testsprite --profile ci --output json auth status
env -u TESTSPRITE_API_KEY testsprite --profile ci --output json project list --max-items 100
```

Do not assume a prior command's profile carries forward or that `--profile` defeats the environment key.

`doctor` checks local CLI/account conditions; its failure is not a product-test verdict. `usage` is informational only:

```bash
testsprite --output json usage
```

Treat credit balance as known only if balance fields are actually returned. Portal Billing is authoritative; absence of fields does not mean unlimited or sufficient credits.

## Backend target truth

Released 0.4.0 surfaces conflict:

- shipped implementation and scaffold use an explicit Python `BASE_URL`;
- `--target-url` does not rewrite that backend code;
- bundled vendor skill guidance also mentions `TARGET_URL`.

Use explicit reviewed `BASE_URL`. Do not teach `TARGET_URL` as guaranteed and do not infer retargeting because generic help accepts `--target-url`. Inspect saved code and correlate the observed host from backend result/failure evidence, application request logs, and timestamps.

A public target can use the CLI without MCP. For localhost-only targets, use TestSprite's documented MCP workflow. These local commands install or inspect agent guidance; they are not MCP:

```bash
testsprite agent list
testsprite agent install --help
testsprite --output json agent status
```

Do not invent MCP tool names.

## Project resolution

```bash
testsprite --output json project list --page-size 100 --max-items 100
testsprite --output json project get "$PROJECT_ID"
testsprite --output json project create --type backend --name "service backend"
```

A project has one type. Backend project creation does not require a URL because saved Python carries the target.

An explicit task-supplied project ID is authoritative. `TESTSPRITE_PROJECT_ID` and `.testsprite/config.json` may be repository/skill conventions but are not general CLI defaults. Use them only when the repository documents them.

Use an idempotency key only when safely retrying a mutating command after an ambiguous transport failure. Never reuse one key for different payloads.

## Managed application credentials

Static credential:

```bash
testsprite --output json project credential "$PROJECT_ID" \
  --type "Bearer token" --credential-file "$CREDENTIAL_FILE"

testsprite --output json project credential "$PROJECT_ID" \
  --type "API key" --credential-file "$CREDENTIAL_FILE"

testsprite --output json project credential "$PROJECT_ID" --type public
```

Prefer file options over inline credentials. Inspect current `project auto-auth --help` before configuring recurring auth, and use its secret-file options.

Vendor-shipped backend code contracts include:

- `__AUTH_HEADERS__` — copy into authenticated request headers;
- `__AUTH_CREDENTIAL__` — never expose, print, serialize, or inspect in test code; and
- `__AUTH_TYPE__` — avoid exposing unless a narrowly reviewed non-secret branch truly needs it.

## Inspect and scaffold tests

```bash
testsprite --output json test list --project "$PROJECT_ID" --type backend --max-items 100
testsprite --output json test list --project "$PROJECT_ID" --type backend \
  --status failed,blocked --max-items 100
testsprite test scaffold --type backend --out /tmp/testsprite-test.py
```

`test scaffold` is local and produces a starting point, not a semantically sufficient test. Review explicit target, managed auth, timeouts, cleanup, and assertions.

## Create backend tests

```bash
testsprite --output json test create \
  --project "$PROJECT_ID" --type backend \
  --name "P0 semantic - search returns source URLs" \
  --description "Requires non-empty valid HTTP source URLs" \
  --priority p0 --code-file /tmp/search-sources.py
```

Create and immediately run one narrow test:

```bash
testsprite --output json test create \
  --project "$PROJECT_ID" --type backend --name "P0 health contract" \
  --code-file /tmp/health.py --run --wait --timeout 600
```

For chained `test create --run --wait`, the 0.4.0 JSON response keeps test fields at the top level and run fields under `.run`. Parse `.testId`, `.codeVersion`, `.run.runId`, and `.run.status`; do not expect top-level `.runId` or `.status`.

Use the same idempotency key only to resolve an ambiguous response to the same create payload. List before attempting another create.

## Dependency metadata

Declare backend graph metadata during creation when known:

```bash
testsprite --output json test create --project "$PROJECT_ID" --type backend \
  --name "producer creates resource" --code-file /tmp/create.py \
  --produces resource_id

testsprite --output json test create --project "$PROJECT_ID" --type backend \
  --name "consumer reads resource" --code-file /tmp/read.py \
  --needs resource_id

testsprite --output json test create --project "$PROJECT_ID" --type backend \
  --name "cleanup deletes resource" --code-file /tmp/delete.py \
  --category teardown
```

CLI 0.4.0 can edit `--produces`, `--needs`, and `--category` through `test update`. Do not delete/recreate merely to change graph metadata:

```bash
testsprite test update --help
testsprite --output json test update "$TEST_ID" --produces resource_id
testsprite --output json test update "$TEST_ID" --needs resource_id
testsprite --output json test update "$TEST_ID" --category teardown
```

Before updating, inspect the current test/graph and preserve intended metadata. Confirm the returned state rather than assuming replacement/append semantics.

## Read and update saved code

```bash
umask 077
CODE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/testsprite-code.XXXXXXXX")"
testsprite test code get "$TEST_ID" --out "$CODE_DIR/current.py"
testsprite --output json test code get "$TEST_ID" > "$CODE_DIR/current.json"
testsprite --output json test code put "$TEST_ID" \
  --code-file "$CODE_DIR/fixed.py" --expected-version "$CODE_VERSION"
```

After an update, export the final saved code and returned `codeVersion`, then reconcile the frozen assertion ledger—including cleanup—against that exact version.

Prefer optimistic `--expected-version`. A precondition failure means fetch, reconcile, and retry. Forceful overwrite discards concurrency protection.

| Need | Operation | Rule |
|---|---|---|
| New durable contract | `test create` | Create once after reviewing code |
| Correct saved Python | `test code put --expected-version` | Preserve identity/history |
| Change graph metadata | `test update` | Review current graph; update in place |
| Fast saved-code feedback | `test rerun` | Inspect the full backend closure |
| Final external evidence | `test run` | Individual only when self-contained; graph proof needs one fresh exact-closure batch |

Freeze exact expected IDs, producer/consumer/teardown closure, and assertions before any run. Do not remove a failed member or reclassify scope afterward.

## Run one test

```bash
testsprite --output json test run "$TEST_ID" --wait --timeout 600
```

Without `--wait`, exit 0 may mean queued, not passed. With `--wait`, inspect the returned terminal state.

Exit 7 includes timeout, unsupported operation, and deferred cases. Resume only when stdout contains a real run ID:

```bash
testsprite --output json test wait "$RUN_ID" --timeout 600
```

If no run ID exists, classify the command outcome and do not fabricate a wait target. Do not wrap waits in an unbounded retry loop.

Ctrl-C detaches local polling; it does not stop server execution. When cancellation is authorized:

```bash
testsprite --output json test cancel "$RUN_ID"
```

`test cancel` exits 0 for cancelled or already-cancelled runs, 4 when the run is not found, 6 when an already-terminal run conflicts with cancellation, and may return 1 for a multi-error outcome. A subsequent `test wait` on a cancelled run exits 1. Cancellation does not refund credits; query final server state. Exit 14 is `CLIENT_TOO_OLD`, never cancellation.

## Batch runs: prove exact membership

```bash
testsprite --output json test run --all --project "$PROJECT_ID" \
  --filter "P0" --wait --timeout 600 --max-concurrency 4
```

Before triggering, resolve and record the exact expected test IDs. Exit 0 can coexist with `conflicts`, skipped arrays, or partial membership. A batch is green only when all are true:

1. returned accepted membership equals the expected ID set;
2. `conflicts` is empty;
3. every deferred or skipped array is empty;
4. no expected member is missing and no unexpected member is silently substituted; and
5. every accepted member is terminal `passed`.

Queued, running, blocked, failed, cancelled, deferred, skipped, conflicted, missing, or unknown members keep the batch non-green.

`--max-concurrency` on backend `test run --all --wait` limits client polling only. It does not limit server execution, application traffic, test dispatch, shared-state overlap, or provider pressure. Serialize explicit IDs or use reviewed graph waves when server-side concurrency matters.

JUnit output is a sidecar, not stronger evidence than the JSON membership/status checks:

```bash
testsprite --output json test run --all --project "$PROJECT_ID" \
  --wait --timeout 600 --max-concurrency 4 \
  --report junit --report-file ./testsprite-junit.xml
```

## Rerun and closure handling

```bash
testsprite --output json test rerun "$TEST_ID" --wait --timeout 600
testsprite --output json test rerun "$TEST_ID" \
  --skip-dependencies --wait --timeout 600
testsprite --output json test flaky "$TEST_ID" --runs 3 --until-fail --timeout 600
```

Backend rerun may execute producers and teardowns while the process exit follows only the selected test. Inspect every closure member and `closureFailures[]`. Any failed producer or teardown keeps the rerun non-green even when the selected test or command exits successfully.

Use `--skip-dependencies` only when the selected test is genuinely self-contained. Backend attempts may consume credits. Rerun and flaky checks are feedback, not final proof.

## Backend results and evidence contradiction

Create an unpredictable restricted directory before capturing result, step, code, trace, failure, or artifact output; redirect raw JSON there rather than printing application payloads into the transcript:

```bash
umask 077
EVIDENCE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/testsprite-evidence.XXXXXXXX")"
testsprite --output json test result "$TEST_ID" --include-analysis > "$EVIDENCE_DIR/result.json"
testsprite --output json test result "$TEST_ID" --history --since 24h > "$EVIDENCE_DIR/history.json"
testsprite --output json test steps "$TEST_ID" --run-id "$RUN_ID" --max-items 100 > "$EVIDENCE_DIR/steps.json"
testsprite --output json test diff "$OLD_RUN_ID" "$NEW_RUN_ID" > "$EVIDENCE_DIR/diff.json"
testsprite --output json test failure summary "$TEST_ID" > "$EVIDENCE_DIR/failure-summary.json"
testsprite --output json test failure get "$TEST_ID" --out "$EVIDENCE_DIR/latest-failure"
```

CLI 0.4.0 backend results can include `apiOutput` and `trace`; inspect them only in the restricted directory, treat them as application/runner evidence, and share allowlisted correlation metadata plus sanitized content—not raw payloads.

Backend artifact scope is officially contradictory:

- shipped implementation/scaffold directs backend failures to latest `test failure get TEST_ID`;
- public documentation advertises `test artifact get RUN_ID`.

Do not promise an immutable backend bundle. When installed help and actual output support the public command, it may be attempted:

```bash
testsprite --output json test artifact get "$RUN_ID" \
  --out "$EVIDENCE_DIR/$RUN_ID-artifact"
```

For every result, failure bundle, artifact, `apiOutput`, or `trace`, prove correlation to the pinned run using run ID, saved code version, explicit/observed target, request IDs, and timestamps. When backend wait returns a legacy/test-level fallback, final proof requires parseable equality `runIdIfAvailable == RUN_ID`. Missing, null, mismatched, or unparseable correlation is diagnostic-only unresolved `TestSprite execution failure`; never attribute it to the pinned run or call it passed.

Treat all output as sensitive and keep it out of git.

## Dry-run

```bash
testsprite --dry-run --output json test run "$TEST_ID"
testsprite --dry-run --output json test create \
  --project "$PROJECT_ID" --type backend --name "contract" \
  --code-file /tmp/test.py
```

Dry-run validates client shape. It does not prove TestSprite auth, project existence, code execution, target reachability, application auth, deployment revision, or behavior.

## Exit codes

| Code | Meaning relevant to this workflow | Agent response |
|---:|---|---|
| 0 | Command success; may still be queued or partial | Parse status, membership, conflicts, skips, and closure |
| 1 | Failed/blocked/cancelled or command-specific negative verdict | Classify pinned evidence |
| 2 | Command is not implemented | Do not retry; use a supported documented operation |
| 3 | TestSprite auth/scope error | Check env key or explicit profile/scope |
| 4 | Resource not found/not ready; `test cancel` uses this for missing run | Verify IDs and state |
| 5 | Parse, unknown-command, missing-argument, or validation error | Correct command/input; do not retry unchanged |
| 6 | Conflict/already running; `test cancel` uses this for already-terminal conflict | Use a returned real active run ID or reconcile |
| 7 | Timeout, unsupported operation, or deferred | Wait only if a real run ID was returned |
| 10 | Transport/network unavailable | Retry boundedly; preserve write idempotency |
| 11 | Rate limited | Honor `Retry-After` |
| 12 | Insufficient credits | Check Portal Billing; do not spin |
| 14 | `CLIENT_TOO_OLD` | Upgrade the client; never classify as cancellation |
| 129/130/143 | Local signal/termination | Query server state before retrying or cancelling |

Commands may document narrower subsets. Automation must inspect JSON and drive any triggered run to a terminal state.

## CLI versus Portal scope

Use the CLI for scriptable create/edit/run/result/failure workflows. Use the Portal for its documented visual/discovery/refinement/billing surfaces. Do not invent a CLI subcommand to mirror a Portal control.

## Official TestSprite sources

Primary documentation, accessed 2026-08-03:

- [CLI overview](https://docs.testsprite.com/cli/getting-started/overview)
- [Installation](https://docs.testsprite.com/cli/getting-started/installation)
- [Quickstart](https://docs.testsprite.com/cli/getting-started/quickstart)
- [Authentication](https://docs.testsprite.com/cli/core/authentication)
- [Projects](https://docs.testsprite.com/cli/core/projects)
- [Creating tests](https://docs.testsprite.com/cli/core/creating-tests)
- [Editing tests](https://docs.testsprite.com/cli/core/editing-tests)
- [Running tests](https://docs.testsprite.com/cli/core/running-tests)
- [Reading results](https://docs.testsprite.com/cli/core/reading-results)
- [Rerun and auto-heal](https://docs.testsprite.com/cli/core/rerun-and-auto-heal)
- [Agent integration](https://docs.testsprite.com/cli/core/agent-integration)
- [CI/CD integration](https://docs.testsprite.com/cli/integrations/ci-cd)
- [Command reference](https://docs.testsprite.com/cli/reference/command-reference)
- [Configuration](https://docs.testsprite.com/cli/reference/configuration)
- [Output and scripting](https://docs.testsprite.com/cli/reference/output-and-scripting)
- [Exit codes](https://docs.testsprite.com/cli/reference/exit-codes)
- [Common issues](https://docs.testsprite.com/cli/troubleshooting/common-issues)
- [API testing overview](https://docs.testsprite.com/web-portal/core/api/api-testing)
- [Dependency chains](https://docs.testsprite.com/web-portal/core/api/dependency-chains)
- [Data Flow](https://docs.testsprite.com/web-portal/core/api/data-flow)
- [Refining tests](https://docs.testsprite.com/web-portal/core/working-with-test/refining-tests)

## Troubleshooting commands

| Symptom | Command-first response |
|---|---|
| Old example fails | Read `testsprite COMMAND --help`; do not blame flag position by default |
| Env key works but profile does not | `TESTSPRITE_API_KEY` overrides it; unset env, pass profile, verify identity/scopes |
| Inherited endpoint override exists | Reject unless exact TLS endpoint and credential environment were authorized |
| Wait timed out | Wait only on the real returned run ID |
| Backend override did not change target | Expected; review `BASE_URL` and observed host |
| Batch exit 0 has skipped/conflicted IDs | Keep gate red; require exact terminal membership |
| Selected rerun passed but closure failed | Inspect every member and `closureFailures[]` |
| Ctrl-C left work running | Query run; use authorized `test cancel RUN_ID`, then parse 0/4/6/1 |
| Exit 14 appeared | Upgrade the client; `CLIENT_TOO_OLD` is not cancellation |
| Artifact surface disagrees with docs | Correlate latest evidence or report unresolved scope |
| Usage omits balance | Check Portal Billing |
