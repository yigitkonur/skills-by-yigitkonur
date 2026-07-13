# TestSprite CLI Backend Reference (verified on 0.3.0)

Use this reference for exact backend-oriented commands, output contracts, exit handling, and links to the official TestSprite CLI documentation. Commands were checked against the installed 0.3.0 help on 2026-07-13.

Treat `0.3.0` as the verified floor for these examples, not a timeless latest-version claim. For syntax, installed `--help` wins; for product intent, use the current official docs; for actual behavior, use a bounded dry-run or real pinned run. Record and resolve any disagreement instead of blending the sources.

## Authority and syntax

Run the installed help before relying on remembered syntax:

```bash
testsprite --version
testsprite --help
testsprite test run --help
```

Global flags must appear before the subcommand:

```bash
testsprite --output json test list --project "$PROJECT_ID"
testsprite --dry-run --output json test run "$TEST_ID"
testsprite --profile ci --output json auth status
```

Use this order even when an older example appends `--output json`.

Core global flags:

| Flag | Purpose |
|---|---|
| `--output text|json` | Human or stable machine-readable output |
| `--profile NAME` | Select credentials profile for this invocation |
| `--endpoint-url URL` | Override TestSprite API endpoint; normally leave default |
| `--request-timeout SECONDS` | Bound each CLI API request |
| `--verbose` / `--debug` | Diagnostics; inspect output before sharing |
| `--dry-run` | Preview request/response shape without credentials or mutation |

The JSON contract is additive within a major CLI version. Parse named fields and tolerate unknown fields.

### Backend target truth

The generic CLI exposes `--target-url`, but backend Python carries its own base URL. In the verified 0.3.0 surface:

| Invocation | What to expect |
|---|---|
| `test create --type backend --run --target-url ...` | Accepted with an advisory that the backend target is code-defined |
| `test run TEST --target-url ...` | Generic run accepts the flag, but it does not rewrite saved Python |
| `test run --all --project ... --target-url ...` | Rejected because batch cannot apply a per-run URL override |

Always inspect saved code and completed Data Flow. A generic flag appearing in help is not evidence that an embedded backend URL changed.

## Install, configure, and diagnose

```bash
npm install -g @testsprite/testsprite-cli
testsprite setup
testsprite --output json auth status
testsprite --output json doctor
testsprite --output json usage
```

Current auth commands are `auth status` and `auth remove`. Older `auth whoami`, `auth configure`, and `auth logout` aliases may exist but are deprecated; do not teach them in new automation.

`doctor` checks version, Node, profile, endpoint, credentials, connectivity, and installed agent guidance. Read its individual checks; a nonzero exit is not a product-test result.

`usage` is the proactive credit/entitlement preflight. If the backend does not yet return a balance, inspect the portal billing page rather than assuming unlimited credits.

## Project commands

```bash
testsprite --output json project list --page-size 100 --max-items 100
testsprite --output json project get "$PROJECT_ID"
testsprite --output json project create --type backend --name "service backend"
```

A project has one type. Backend project creation does not require a URL; frontend project creation does. Backend saved Python determines its target. In 0.3.0, `--target-url` is accepted by generic run syntax but ignored for backend tests.

Use an explicit idempotency key only when safely retrying a mutating CLI command after an ambiguous transport failure:

```bash
testsprite --output json project create --type backend --name "service backend" \
  --idempotency-key "project-create-service-backend-v1"
```

Do not reuse one idempotency key for different payloads.

## Managed backend credentials

Static credential, free tier:

```bash
testsprite --output json project credential "$PROJECT_ID" \
  --type "Bearer token" --credential-file "$CREDENTIAL_FILE"

testsprite --output json project credential "$PROJECT_ID" \
  --type "API key" --credential-file "$CREDENTIAL_FILE"

testsprite --output json project credential "$PROJECT_ID" --type public
```

Accepted types in 0.3.0 are `public`, `Bearer token`, `API key`, and `basic token`. Prefer `--credential-file`; the inline `--credential` option can expose secrets in shell/process history.

Auto-refresh authentication is a Pro feature. Inspect current method help before configuration:

```bash
testsprite project auto-auth --help
```

Supported 0.3.0 methods are `password`, `refresh_token`, and `aws_cognito_refresh`, with injection into Bearer, header, or cookie. Prefer `--password-file`, `--client-secret-file`, and `--refresh-token-file` over inline values.

## Inspect and scaffold tests

```bash
testsprite --output json test list --project "$PROJECT_ID" \
  --type backend --max-items 100
testsprite --output json test list --project "$PROJECT_ID" \
  --type backend --status failed,blocked --max-items 100
testsprite test scaffold --type backend --out /tmp/testsprite-test.py
```

`test scaffold` is pure-local: it needs no credentials and makes no network call. The generated Python is a starting point, not a sufficient semantic test.

## Create backend tests

```bash
testsprite --output json test create \
  --project "$PROJECT_ID" --type backend \
  --name "P0 semantic - search returns source URLs" \
  --description "Requires non-empty valid HTTP source URLs" \
  --priority p0 --code-file /tmp/search-sources.py
```

Code files are Python and at most 350 KB. In code-file mode, `--project`, `--type`, `--name`, and `--code-file` are required.

Create and immediately run one test:

```bash
testsprite --output json test create \
  --project "$PROJECT_ID" --type backend --name "P0 health contract" \
  --code-file /tmp/health.py --run --wait --timeout 600
```

Use `--idempotency-key` for a safe retry after an ambiguous create response. Do not issue repeated creates with different keys; that produces duplicates.

## Declare dependencies at creation

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

`--produces` and `--needs` are repeatable. These flags and cleanup category are backend-only, create-only metadata in 0.3.0. The wave engine uses them for `test run --all` and backend reruns.

## Read and update saved code

```bash
testsprite test code get "$TEST_ID" --out /tmp/testsprite-current.py
testsprite --output json test code get "$TEST_ID"
testsprite --output json test code put "$TEST_ID" \
  --code-file /tmp/testsprite-fixed.py --expected-version "$CODE_VERSION"
```

Text output with `--out` writes source. JSON output exposes the wire envelope and code version. Prefer optimistic `--expected-version`; a 412/precondition failure means fetch the current version, reconcile edits, and retry. `--force` discards concurrency protection and is audit-logged.

## Choose reuse, edit, rerun, or fresh run

| Need | Operation | Rule |
|---|---|---|
| New contract not represented in the suite | `test create` | Create once after reviewing generated/authored code |
| Existing test expresses the right intent but code is wrong | `test code put --expected-version` | Preserve identity/history; make the smallest correction |
| Fast feedback using saved code and dependency closure | `test rerun` | No new code generation; backend attempts may consume credits |
| Final regression/release evidence | `test run` | Fresh strict run after the intended revision is deployed |
| Product contract deliberately changed | Portal refinement or reviewed `code put` | Inspect regenerated code and new `codeVersion`; do not auto-accept weaker assertions |

Do not recreate durable tests on every implementation change. TestSprite's value compounds when stable consumer contracts survive refactors.

## Run one test

```bash
testsprite --output json test run "$TEST_ID" \
  --wait --timeout 600
```

Without `--wait`, exit 0 means queued, not passed. With `--wait`, the CLI polls to a terminal state or deadline. Ctrl-C stops local polling but does not cancel the server run; there is no CLI cancel command in 0.3.0.

Backend targeting is code-defined. An individual dry-run cannot resolve the saved test type, so accepting a generic override or showing a synthetic target does not prove that backend Python was retargeted:

```bash
testsprite --dry-run --output json test run "$TEST_ID" \
  --target-url "https://other-environment.example"
# generic command shape only; inspect saved backend code and real Data Flow
```

On exit 7, stdout retains the run ID. Resume that run:

```bash
testsprite --output json test wait "$RUN_ID" --timeout 600
```

Do not wrap `--wait` in a retry loop. On transport exit 10, retry the read/wait command; use idempotency for ambiguous mutating commands.

## Fresh batch run

```bash
testsprite --output json test run --all --project "$PROJECT_ID" \
  --filter "P0" --wait --timeout 600 --max-concurrency 4
```

The fresh batch runs producers before consumers and teardown last. Important limits:

- `--target-url` does not rewrite backend test code, and batch run rejects the flag;
- each backend test is a billable run;
- `--max-concurrency` limits in-flight CLI trigger/poll work, not application-internal concurrency; and
- deferred tests appear separately and force a nonzero exit.

JUnit sidecar:

```bash
testsprite --output json test run --all --project "$PROJECT_ID" \
  --wait --timeout 600 --max-concurrency 4 \
  --report junit --report-file ./testsprite-junit.xml \
  --report-suite-name "service API"
```

## Rerun and flakiness

```bash
testsprite --output json test rerun "$TEST_ID" --wait --timeout 600
testsprite --output json test rerun "$TEST_ID" \
  --skip-dependencies --wait --timeout 600
testsprite --output json test flaky "$TEST_ID" --runs 3 --until-fail --timeout 600
```

Backend rerun executes the saved code plus its producer/teardown closure and may consume credits. `--skip-dependencies` is safe only for a self-contained test. Auto-heal applies to frontend reruns; it is ignored for backend. `test flaky` uses strict replays and backend attempts may consume credits.

Use rerun for fast feedback. Use fresh `test run` for final pass-rate/release evidence.

## Read results and evidence

```bash
testsprite --output json test result "$TEST_ID" --include-analysis
testsprite --output json test result "$TEST_ID" --history --since 24h
testsprite --output json test steps "$TEST_ID" --run-id "$RUN_ID" --max-items 100
testsprite --output json test diff "$OLD_RUN_ID" "$NEW_RUN_ID"
testsprite --output json test failure summary "$TEST_ID"
testsprite --output json test failure get "$TEST_ID" --out /tmp/latest-failure
mkdir -p .testsprite/runs
testsprite --output json test artifact get "$RUN_ID" \
  --out ".testsprite/runs/$RUN_ID"
```

Distinguish pointers from immutable evidence:

| Command | Meaning |
|---|---|
| `test result TEST` | Latest result pointer |
| `test result TEST --history` | Prior runs with cursors |
| `test steps TEST --run-id RUN` | Steps scoped to one run |
| `test failure summary TEST` | One-screen latest-failure summary |
| `test failure get TEST` | Latest failing-run bundle |
| `test artifact get RUN` | Immutable bundle for one run |
| `test diff RUN_A RUN_B` | Verdict/step/code-version regression comparison |

The parent of an artifact output directory must exist. Treat bundles as sensitive and keep them out of git.

## Dry-run

Every command accepts global `--dry-run`:

```bash
testsprite --dry-run --output json test run "$TEST_ID"
testsprite --dry-run --output json test create \
  --project "$PROJECT_ID" --type backend --name "contract" \
  --code-file /tmp/test.py
testsprite --dry-run --output json test code put "$TEST_ID" \
  --code-file /tmp/test.py --expected-version v3 \
  --dry-run-simulate-error PRECONDITION_FAILED
```

Dry-run validates client-side shape and shows a synthetic response. It does not prove TestSprite authentication, project existence, code execution, target reachability, application authentication, deployment revision, or product behavior.

## Exit codes

| Code | Meaning | Agent response |
|---:|---|---|
| 0 | Success; with no `--wait`, possibly only queued | Read returned status before claiming pass |
| 1 | Failed, blocked, cancelled, or command-specific negative verdict | Inspect result/artifact |
| 2 | Usage/unknown command | Re-read installed help |
| 3 | TestSprite authentication/scope error | Run auth status; fix profile/scope |
| 4 | Resource not found/not ready | Verify IDs and run state |
| 5 | Validation error | Correct flags/input; do not retry unchanged |
| 6 | Conflict/already running | Use returned active run ID or reconcile edit |
| 7 | Timeout/deferred | Resume same run with `test wait` |
| 10 | Transport/network unavailable | Retry boundedly; preserve idempotency |
| 11 | Rate limited | Honor `Retry-After` |
| 12 | Insufficient credits | Check usage/plan; do not spin retries |
| 129 | Hangup signal | Determine whether server run continues |
| 130 | Interrupt/Ctrl-C | Reattach with `test wait` if run was triggered |
| 143 | Terminated | Query run state before retrying |

Commands document narrower subsets, but automation should handle the complete global contract.

## Agent integration

```bash
testsprite agent list
testsprite agent install --help
testsprite --output json agent status
```

Agent install is pure-local; status can gate whether installed TestSprite guidance matches the CLI. Repository instructions remain authoritative when generic installed guidance conflicts.

## CLI versus Portal scope

The Web Portal exposes API discovery, plan review, natural-language refinement, Data Flow visualization, dynamic variables, dependency graphs, automatic cleanup views, schedules, billing, and credential management. Some data is shared with CLI tests and runs; not every Portal action has a CLI command.

Use the CLI for scriptable create/edit/run/result/artifact workflows. Use the Portal when a task explicitly requires its visual discovery, refinement, or schedule surfaces. Never invent a CLI subcommand to mirror a Portal button.

## What not to invent

The CLI does not currently expose every Portal feature. Do not fabricate commands for schedules, monitoring management, billing writes, site crawling, test-list/suite management, per-step regeneration, or run cancellation. Check `testsprite --help` and the Portal for current availability.

## Official CLI sources

All links below are TestSprite primary documentation, accessed 2026-07-13:

### Getting started and concepts

- [CLI overview](https://docs.testsprite.com/cli/getting-started/overview)
- [Installation](https://docs.testsprite.com/cli/getting-started/installation)
- [Quickstart](https://docs.testsprite.com/cli/getting-started/quickstart)
- [Key terms](https://docs.testsprite.com/cli/concepts/key-terms)
- [The agent loop](https://docs.testsprite.com/cli/concepts/the-agent-loop)

### Core workflow

- [Authentication](https://docs.testsprite.com/cli/core/authentication)
- [Projects](https://docs.testsprite.com/cli/core/projects)
- [Creating tests](https://docs.testsprite.com/cli/core/creating-tests)
- [Editing tests](https://docs.testsprite.com/cli/core/editing-tests)
- [Running tests](https://docs.testsprite.com/cli/core/running-tests)
- [Reading results](https://docs.testsprite.com/cli/core/reading-results)
- [Rerun and auto-heal](https://docs.testsprite.com/cli/core/rerun-and-auto-heal)
- [Agent integration](https://docs.testsprite.com/cli/core/agent-integration)
- [CI/CD integration](https://docs.testsprite.com/cli/integrations/ci-cd)

### Reference and troubleshooting

- [Command reference](https://docs.testsprite.com/cli/reference/command-reference)
- [Configuration](https://docs.testsprite.com/cli/reference/configuration)
- [Output and scripting](https://docs.testsprite.com/cli/reference/output-and-scripting)
- [Exit codes](https://docs.testsprite.com/cli/reference/exit-codes)
- [What is included](https://docs.testsprite.com/cli/reference/whats-included)
- [Common issues](https://docs.testsprite.com/cli/troubleshooting/common-issues)

### API Portal evidence surfaces

- [API testing overview](https://docs.testsprite.com/web-portal/core/api/api-testing)
- [API discovery](https://docs.testsprite.com/web-portal/core/api/api-discovery)
- [Dependency chains](https://docs.testsprite.com/web-portal/core/api/dependency-chains)
- [Data Flow](https://docs.testsprite.com/web-portal/core/api/data-flow)
- [Auto Cleanup](https://docs.testsprite.com/web-portal/core/api/auto-cleanup)
- [API rerun](https://docs.testsprite.com/web-portal/core/api/api-rerun)
- [Refining tests](https://docs.testsprite.com/web-portal/core/working-with-test/refining-tests)

## Troubleshooting commands

| Symptom | Command-first response |
|---|---|
| Command copied from old docs fails | `testsprite COMMAND --help`; move global flags before subcommand |
| Auth unexpectedly missing | `testsprite --output json auth status` and inspect profile/scopes |
| Project/test not found | list with JSON and verify active profile/project ID |
| Create response was lost | retry with the same idempotency key, then list before creating again |
| Wait timed out | `testsprite --output json test wait "$RUN_ID"` |
| Artifact says not ready | wait for terminal failure, then retry artifact once |
| Backend run did not use target override | Expected; update saved Python or use an environment-specific test |
| Backend rerun used credits | Expected; only frontend saved-script replay is free |
| Portal regenerated a weaker assertion | Export the new code/version, restore the contract, and rerun; refinement is not automatic approval |
| A Portal feature has no matching command | Use the Portal or current documented surface; do not fabricate CLI syntax |
