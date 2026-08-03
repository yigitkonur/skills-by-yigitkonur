---
name: run-testsprite-frontend
description: Use skill if you are creating, running, debugging, or release-gating TestSprite frontend browser tests, including public-target CLI or localhost MCP routing; not backend, load, security, or local-unit testing.
---

# Run TestSprite Frontend

Use TestSprite as an independent cloud browser against an authorized frontend target. Discover repository truth, freeze the verification contract, run exact tests to terminal verdicts, fix the demonstrated layer, deploy the exact artifact, and prove it with a newly triggered run.

For TestSprite backend API work, hand off to the sibling `run-testsprite-backend` skill. Do not adapt this frontend workflow to backend tests.

## Non-negotiable rules

1. Read repository and deployment policy before changing code, TestSprite state, a target, or MCP configuration.
2. Treat every network write, billable run, deployment, project create/update, plan/code/create/cancel operation, MCP mutation, browser mutation, and application side effect as blocked until explicitly authorized.
3. Record authorization scope: account/profile, project/test IDs, exact target origin, intended effect, concurrency, cleanup, rollback/restoration, and retention.
4. Inherit `TESTSPRITE_API_KEY` without printing or persisting it. Reject inherited endpoint overrides unless the exact TLS endpoint and credential environment are separately authorized.
5. Bind application login/project credentials to the explicitly authorized target origin. Never put credentials in target URLs, plans, source, arguments, logs, or transcripts.
6. Use the CLI only for public HTTP(S) targets. Treat localhost/private-only MCP as an exceptional, disposable, explicitly authorized workflow.
7. Freeze required test IDs and plan identities before execution. Removing, weakening, or reclassifying one after failure changes the contract; it is not remediation.
8. Preserve terminal JSON and run-scoped steps for every run. Preserve an artifact for failed/blocked runs when available, under restricted temporary storage.
9. Final proof must trigger a newly queued run after deployment proof, capture its new run ID/enqueue time/target/code version, and then wait that exact run to a fresh terminal pass.

## Reference router

| Situation | Read |
|---|---|
| Repository entry, target/account choice, endpoint controls, or revision proof | [references/repository-and-target.md](references/repository-and-target.md) |
| Plan authoring, fixed coverage contract, credentials, mutations, or auditor findings | [references/plan-and-coverage.md](references/plan-and-coverage.md) |
| Exact CLI 0.4.0 commands, auth precedence, create/batch/run/rerun/evidence behavior | [references/cli-reference.md](references/cli-reference.md) |
| Failure classification, auto-heal, deployment, evidence, or release gate | [references/failure-and-release.md](references/failure-and-release.md) |
| Localhost/private target or explicit MCP request | [references/mcp-localhost.md](references/mcp-localhost.md) |

Read every routed reference needed for the task. All five references are part of this skill; do not substitute remembered vendor syntax.

## Workflow

### 1. Freeze the verification and authorization contract

Record before remote or billable action:

- user-visible behavior and exact required test IDs/plan identities;
- authorized TestSprite account/profile, project ID/type, and expected saved code version;
- exact public target origin and expected immutable revision/release;
- application account/role/tenant and how credentials are origin-bound;
- allowed writes, browser actions, external systems, concurrency, cleanup, rollback, and retention;
- pass condition and recognized non-product gates.

Predeclare outcomes: `verified`, `product defect`, `plan defect`, `generated-code defect`, `deployment drift`, `auth/environment defect`, `external gate`, or `runner defect`. Do not redefine success after observing failure.

### 2. Discover repository, deployment, and existing TestSprite truth

Read the nearest instructions, routes/pages, product contracts, native browser tests, fixtures, auth helpers, deployment workflow, revision surfaces, and existing TestSprite project/test/history/code evidence. Trace one critical journey from entry through visible outcome and cleanup.

Prefer an immutable preview/release URL. If only a mutable URL exists, require request-correlated release evidence that excludes A→B→A drift during the browser run; equal before/after fingerprints alone are insufficient. Follow [repository and target discovery](references/repository-and-target.md).

### 3. Select public CLI or fail-closed MCP

| Target | Route |
|---|---|
| Authorized public preview/staging/canary/production | Pinned CLI workflow |
| Localhost/private-only | [Disposable MCP workflow](references/mcp-localhost.md), only after explicit authorization |
| Approved public preview/tunnel can be created | Deploy/create through repository policy, prove revision, then use CLI |
| No faithful reachable target or disposable MCP boundary | Stop at repository-native evidence; report TestSprite runtime proof blocked |

`testsprite agent install` writes local instructions; it is not MCP setup.

### 4. Use the exact pinned CLI independently

CLI 0.4.0 requires Node `^20.19.0 || ^22.13.0 || >=24`. Never define a shell function or rely on `TS_PROFILE`, `TESTSPRITE_PROFILE`, or prior Bash state. Every example invocation is self-contained and pins the package:

```bash
node --version
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --version
```

Use a concrete profile on every network invocation. Examples use `default`; replace it consistently with the authorized profile name when needed.

Reject credential-routing overrides before authentication without printing their values:

```bash
[ -n "${TESTSPRITE_API_KEY:-}" ] || { printf '%s\n' 'TESTSPRITE_API_KEY is not injected' >&2; exit 1; }
[ -z "${TESTSPRITE_API_URL:-}" ] || { printf '%s\n' 'Unapproved TESTSPRITE_API_URL is set' >&2; exit 1; }
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json auth status
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json doctor
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json usage
```

An inherited `TESTSPRITE_API_KEY` overrides the selected stored profile key. To deliberately use an authorized stored profile, unset the inherited key for that invocation and verify returned identity/scopes before any write or run:

```bash
env -u TESTSPRITE_API_KEY npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json auth status
```

Ordinary injected-key use needs no setup. If persistent setup is separately authorized, the exact noninteractive form is:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default setup --no-agent --from-env
```

This persists the inherited key. Plain `setup --no-agent` is interactive only. Never persist as a convenience.

### 5. Resolve project, target, and frozen tests

Read-only discovery still requires the authorized credential route:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json project list --max-items 100
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json project get "<PROJECT_ID>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test list --project "<PROJECT_ID>" --type frontend --max-items 200
```

Project list/get does not reliably reveal the stored frontend URL. Prefer individual fresh runs with explicit target URLs. Update/create a project only under the authorization/restoration gate in [the CLI reference](references/cli-reference.md). Freeze the complete release-gating test ID set and plan/code identities before execution.

### 6. Author and audit declarative plans

Start from the pinned local scaffold:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite test scaffold --type frontend --out "<PLAN_FILE>"
```

Plans contain intent and observable assertions, never selectors or credentials. Resolve the loaded skill directory to its actual absolute path; never pass `{baseDir}` literally:

```bash
python3 "/resolved/absolute/path/to/run-testsprite-frontend/scripts/audit_frontend_plan.py" --json "<PLAN_FILE>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --output json test lint --plan-from "<PLAN_FILE>"
```

Authorize outward actions per zero-based step, never globally:

```bash
python3 "/resolved/absolute/path/to/run-testsprite-frontend/scripts/audit_frontend_plan.py" --json --authorized-outward-step 1 --authorized-outward-step 4 "<PLAN_FILE>"
```

The flag records routing, not authorization. Review every warning against the authorization ledger. See [plan and coverage design](references/plan-and-coverage.md).

### 7. Create without conflating creation and proof

Create the reviewed test without running it, then capture the created test ID and verify its plan identity:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test create --plan-from "<PLAN_FILE>" > "/absolute/restricted/run-dir/create.json"
```

If `test create --run` is deliberately used for non-final feedback, run fields are nested under `.run` in JSON; the created test remains at the top level. Do not mistake top-level creation success for a terminal browser verdict.

### 8. Trigger, capture, then wait exact runs

Never combine final trigger and wait. After deployment proof, invoke fresh `test run` without `--wait`, redirect raw JSON into a `umask 077` unpredictable directory, and inspect only allowlisted metadata:

```bash
umask 077
run_dir="$(mktemp -d "${TMPDIR:-/tmp}/testsprite-run.XXXXXXXX")"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test run "<TEST_ID>" --target-url "<AUTHORIZED_PUBLIC_TARGET_URL>" > "$run_dir/queued.json"
printf '%s\n' "$run_dir"
```

Execute that block as one shell invocation. For later calls, use the recorded absolute directory path rather than relying on `run_dir` persistence.

Require a newly queued run ID and enqueue time after deployment proof, with returned target and `codeVersion` matching the frozen contract. A `run_in_flight` conflict or auto-attachment is reconciliation only: wait the attached run to terminal state, collect evidence, then trigger a new run for proof.

Wait only the exact newly created run:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test wait "<NEW_RUN_ID>" --timeout 600 > "/absolute/restricted/run-dir/terminal.json"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test steps "<TEST_ID>" --run-id "<NEW_RUN_ID>" --max-items 200 > "/absolute/restricted/run-dir/steps.json"
```

For failed/blocked runs, request the run artifact when available. Exit 4 for cancelled/no-failure artifact is expected and means no failure bundle exists:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test artifact get "<RUN_ID>" --out "/absolute/restricted/run-dir/artifact"
```

Do not print raw DOM, screenshots, video, forms, URLs with data, generated code, steps, or artifacts into transcripts. Share only allowlisted identifiers/statuses and sanitized excerpts. Retain or upload evidence only with explicit authorization.

### 9. Classify and fix the demonstrated layer

- **Product:** add the required native regression, fix root cause, obtain exact-SHA CI, deploy with authorization, and prove it live.
- **Plan:** preserve the frozen contract, correct erroneous intent, lint, `test plan put`, then fresh-run; changing required coverage is a separately authorized contract change.
- **Generated code:** export current Python/codeVersion, make the smallest reviewed correction, update optimistically, use rerun only for feedback, then fresh-run.
- **Deployment:** correct target/revision evidence before spending another run.
- **Auth/environment/external gate:** fix only authorized accounts, fixtures, sandbox resources, or configuration; never embed credentials or bypass gates.
- **Runner:** preserve IDs and bounded diagnostics; do not patch product code without a faithful app observation.

After `plan put`, always use a fresh run. Auto-heal persistence is unresolved: compare saved source and `codeVersion` before/after, review the healed path, and explicitly persist the correction when needed. Never use auto-heal as release proof.

Rerun has no target override and always uses the current project URL. Verify returned target. If the project URL cannot be changed/restored safely, skip rerun.

### 10. Expand without partial-batch false greens

Use a two-phase batch:

1. Freeze the exact ordered input manifest and expected plan identities.
2. Lint every input plan individually.
3. Run `test create-batch` without `--run`.
4. Require summary `total`, `created`, and `failed`, with `failed=0`, `created=total`, and exactly one unique created test ID mapped to each input.
5. Capture the complete ID set; run each ID separately with trigger-then-wait and explicit target.

Never present `create-batch --run --wait` as proof. Never remove a failed member after execution. `test run --all --target-url ...` is rejected with exit 5; it is not ignored. Broad `--all` is valid only after an authorized project-URL update and complete terminal accounting, but explicit IDs remain preferred.

### 11. Finish with fresh terminal passes

For every frozen release-gating ID:

1. Prove exact-SHA native CI and authorized deployment.
2. Prove an immutable target revision, or request-correlated evidence excluding A→B→A drift.
3. Trigger a fresh run without `--wait` after that proof.
4. Verify new run ID/enqueue time, expected target, and expected `codeVersion`.
5. Wait that exact run to terminal `passed`.
6. Preserve terminal JSON and run-scoped steps; fetch failure artifact when applicable.
7. Re-prove the same revision/release after the run and verify cleanup.

Repeat the fix/deploy/trigger/wait loop until every frozen required test has a fresh terminal pass or remains an explicitly named external gate. Do not claim proof from dispatch, rerun, auto-heal, cancellation, stale deployment, partial batch, moving latest result, or weakened assertions.

## Completion record

Record source SHA/CI, deployment/release identity, target origin, ABA defense, TestSprite CLI/profile/account/project, frozen test IDs/plan identities, expected and run `codeVersion`, new run IDs/enqueue times, terminal statuses, run-scoped evidence paths, classification/fix, authorization scope, cleanup/rollback, retention decision, and remaining gates.
