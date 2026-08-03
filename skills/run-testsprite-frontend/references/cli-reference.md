# TestSprite Frontend CLI 0.4.0 Reference

Use this for released `@testsprite/testsprite-cli@0.4.0` frontend command shapes. Repository policy, explicit authorization, credential routing, and retention gates still apply.

## Invocation and authentication

Pinned facts:

- package: `@testsprite/testsprite-cli@0.4.0`;
- binary: `testsprite`;
- Node: `^20.19.0 || ^22.13.0 || >=24`.

Do not define a shell wrapper or rely on variables/functions from an earlier Bash call. Use the full pinned invocation every time. A repository may instead use a pinned global install only when that persistent tool installation is explicitly authorized.

Use a concrete `--profile` on every network invocation. Examples use `default`; substitute the authorized profile name consistently. Released 0.4.0 does not reliably honor `TESTSPRITE_PROFILE`.

```bash
node --version
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --version
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --help
```

Reject inherited routing overrides by default:

```bash
[ -n "${TESTSPRITE_API_KEY:-}" ] || { printf '%s\n' 'TESTSPRITE_API_KEY is not injected' >&2; exit 1; }
[ -z "${TESTSPRITE_API_URL:-}" ] || { printf '%s\n' 'Unapproved TESTSPRITE_API_URL is set' >&2; exit 1; }
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json auth status
```

`TESTSPRITE_API_URL`, CLI `--endpoint-url`, MCP `API_URL`, and tunnel endpoint overrides control where credentials travel. Permit an override only for an exact authorized TLS endpoint and a matching credential environment. Do not mix production credentials with a staging/custom endpoint.

An inherited `TESTSPRITE_API_KEY` overrides the stored key selected by `--profile`. To use an authorized stored profile, remove the inherited key only for that command and verify returned identity/scopes before acting:

```bash
env -u TESTSPRITE_API_KEY npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json auth status
```

Ordinary inherited-key commands require no setup. Persistent setup is a credential write and is blocked without separate explicit authorization. Exact noninteractive inherited-key persistence:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default setup --no-agent --from-env
```

Plain `setup --no-agent` is interactive only. Never create `.env`/`.envrc`, print the key, or persist a profile as a convenience.

## General authorization gate

Before project create/update, test create/plan/code/cancel, billable run/rerun/flaky, deployment, MCP/browser mutation, or application side effect, record:

- authorized TestSprite identity/profile and credential endpoint;
- project/test/run IDs;
- exact target origin and application credential binding;
- intended cloud/application effect and credit use;
- concurrency/account isolation;
- cleanup and rollback/restoration;
- evidence retention and sharing scope.

A command example is never authorization.

## Local scaffold and lint

These commands are local and do not need credentials:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite test scaffold --type frontend --out "<PLAN_FILE>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --output json test lint --plan-from "<PLAN_FILE>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --output json test lint --steps "<STEPS_FILE>"
```

Plan input is at most 256 KiB. Vendor lint exits 0 when valid and 5 when invalid.

## Project and test discovery

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json project list --max-items 100
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json project get "<PROJECT_ID>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test list --project "<PROJECT_ID>" --type frontend --max-items 200
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test get "<TEST_ID>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test result "<TEST_ID>" --history --since 7d
```

Project list/get does not reliably expose the stored frontend URL. Freeze exact required test IDs and plan/code identities before execution.

## Project create/update and login credentials

Prefer individual fresh runs with explicit target URLs. Create/update project state only after the general authorization gate and when the project is dedicated, or when the prior URL, concurrent-user safety, restoration, and rollback are known.

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json project create --type frontend --name "<PROJECT_NAME>" --url "<AUTHORIZED_PUBLIC_TARGET_URL>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json project update "<PROJECT_ID>" --url "<AUTHORIZED_PUBLIC_TARGET_URL>"
```

The URL must be public HTTP(S), not localhost/private. Bind optional application login/project credentials to that exact authorized origin. Never use credential-bearing URLs or inline passwords; use an authorized protected password file only when the CLI workflow explicitly supports it. Verify the next completed run's returned target, then restore prior project state when authorized procedure requires it.

If prior URL/restoration is unknown, do not mutate a shared project merely to enable rerun or `--all`.

## Create one test

A full plan owns `projectId`, `type`, `name`, optional `description`/`priority`, and `planSteps`. Omit redundant metadata flags in plan mode.

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test create --plan-from "<PLAN_FILE>" > "/absolute/restricted/run-dir/create.json"
```

Creation does not prove browser behavior. If authorized non-final feedback deliberately uses `test create --run`, its JSON keeps created-test fields at the top level and nests run fields under `.run`. Read `.run.runId`, `.run.status`, `.run.targetUrl`, and `.run.codeVersion`; do not look for those run fields at the top level. Without `--wait`, `.run` is dispatch state only.

## Two-phase batch creation

Never use chained `create-batch --run --wait` as release proof.

1. Freeze the exact ordered input manifest and expected identity for every plan.
2. Lint every plan separately, so every input has an explicit lint result.
3. Create without `--run`:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test create-batch --plan-from-dir "<PLAN_DIR>" > "/absolute/restricted/run-dir/batch-create.json"
```

Or, for JSONL:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test create-batch --plans "<JSONL_FILE>" > "/absolute/restricted/run-dir/batch-create.json"
```

Require reported `total`, `created`, and `failed`; `failed` must be zero, `created` must equal `total`, and exactly one unique created test ID must map to each expected input. Capture the complete ID set before running any member. Then trigger and wait each ID separately.

Limits: frontend only, at most 50 specs/files, at most 5 MiB total, and mutually exclusive `--plans`/`--plan-from-dir`. `--max-concurrency` controls dispatch/polling, not application state safety.

## Fresh individual run: trigger then wait

Final and release-gating runs must be two commands.

Trigger after deployment/revision proof, without `--wait`:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test run "<TEST_ID>" --target-url "<AUTHORIZED_PUBLIC_TARGET_URL>" > "/absolute/restricted/run-dir/queued.json"
```

Require a newly queued run ID and enqueue timestamp after deployment proof, expected target, and expected `codeVersion`. Exit 0 means accepted/queued, not passed.

A `run_in_flight` conflict or auto-attachment is not a fresh proof run. Wait/reconcile the attached run to terminal state, collect its evidence, then trigger again and require a new ID.

Wait that exact new run:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test wait "<NEW_RUN_ID>" --timeout 600 > "/absolute/restricted/run-dir/terminal.json"
```

A wait timeout does not justify a duplicate trigger; resume the same run ID. Ctrl-C detaches and does not cancel server execution.

## Broad fresh run

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test run --all --project "<PROJECT_ID>" --wait --timeout 600
```

Passing `--target-url` with `test run --all` is rejected with exit 5; it is not ignored. Use broad `--all` only after an authorized project URL update and only when terminal JSON accounts for every frozen frontend test with no conflicts, deferred/missing members, partial polling, or `skippedFrontend`. Explicit individual IDs are safer.

## Rerun, strict replay, and auto-heal

Rerun accepts no target override and always uses the current project URL. Verify the returned target. If the current project URL cannot be established or safely changed/restored, skip rerun.

Strict saved-script feedback:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test rerun "<TEST_ID>" --no-auto-heal --wait --timeout 600 > "/absolute/restricted/run-dir/strict-rerun.json"
```

Default auto-heal feedback:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test rerun "<TEST_ID>" --wait --timeout 600 > "/absolute/restricted/run-dir/healed-rerun.json"
```

Neither is final proof. Auto-heal persistence in 0.4.0 is unresolved: capture saved source and `codeVersion` before/after, compare exact-run steps, and explicitly persist the reviewed correction when saved state did not become the intended durable state.

After `test plan put`, use a fresh run. Rerun may replay code generated before the replacement plan.

## Replace plan steps

Audit and lint a `{ "planSteps": [...] }` file, then update with optimistic step-count protection:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --output json test lint --steps "<STEPS_FILE>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test plan put "<TEST_ID>" --steps "<STEPS_FILE>" --expected-step-count "<CURRENT_STEP_COUNT>"
```

A 412 means the plan changed; reconcile rather than forcing overwrite. Trigger a fresh run after every successful plan replacement.

## Read and replace generated Python

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default test code get "<TEST_ID>" --out "/absolute/restricted/run-dir/current.py"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test code get "<TEST_ID>" > "/absolute/restricted/run-dir/current-code.json"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test code put "<TEST_ID>" --code-file "/absolute/restricted/run-dir/reviewed.py" --expected-version "<CODE_VERSION>"
```

Current source is attributable to an older pinned run only when versions match. Otherwise use run-scoped source when available or mark executed source unresolved. Plans own intent; generated code owns selectors/mechanics.

## Exact-run evidence and restricted storage

Set `umask 077` and allocate an unpredictable directory before capture:

```bash
umask 077
mktemp -d "${TMPDIR:-/tmp}/testsprite-run.XXXXXXXX"
```

Use the returned absolute path explicitly in later commands. Preserve terminal JSON and steps for every run:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test steps "<TEST_ID>" --run-id "<RUN_ID>" --max-items 200 > "/absolute/restricted/run-dir/steps.json"
```

Fetch an artifact for failed/blocked runs when available:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test artifact get "<RUN_ID>" --out "/absolute/restricted/run-dir/artifact"
```

Artifact exit 4 for cancelled/no-failure runs is expected and means no failure bundle is available. `test result TEST` and `test failure get TEST` are moving latest pointers, not exact-run proof.

Raw terminal JSON, steps, DOM, screenshots, video, forms, URLs/data, reports, and generated code may contain sensitive material. Do not print them to transcripts. Share allowlisted metadata and sanitized excerpts only. Retention/upload requires explicit authorization.

## Cancellation

Cancel only a task-owned run with explicit authorization, then verify terminal server state:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test cancel "<RUN_ID>" > "/absolute/restricted/run-dir/cancel.json"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test wait "<RUN_ID>" --timeout 60 > "/absolute/restricted/run-dir/cancel-terminal.json"
```

Read every cancelled/already-cancelled/conflict/not-found/error category. A cancelled terminal wait can return a nonzero product-verdict exit. Credits already charged are not refunded.

## Exit discipline

| Condition | Required response |
|---|---|
| Exit 0 without wait | Dispatch only; verify new ID and wait it |
| `run_in_flight`/attachment | Reconcile attached run, then trigger a new proof run |
| Terminal pass | Verify target, code version, revision, steps, and frozen contract |
| Failed/blocked/cancelled | Preserve terminal JSON/steps; request artifact when available |
| Timeout/deferred | Resume same run |
| Auth/config/exit 5 validation | Correct input/routing; do not retry unchanged |
| Artifact exit 4 | Expected no-failure/no-artifact state |
| Insufficient credits | Stop and report account gate |

Parse named JSON fields and tolerate additive unknown fields.

## Vendor sources

Verified on 2026-08-03 against supplied released-0.4.0 research and current vendor pages:

- [Creating tests](https://docs.testsprite.com/cli/core/creating-tests)
- [Command reference](https://docs.testsprite.com/cli/reference/command-reference)
- [What is included](https://docs.testsprite.com/cli/reference/whats-included)

If a later pinned CLI differs, inspect its help, research the new version, and update this skill rather than blending versions.
