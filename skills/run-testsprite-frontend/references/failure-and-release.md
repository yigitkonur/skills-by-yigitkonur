# Failure Diagnosis, Fix, Deployment, and Release Proof

Read after any failed, blocked, healed, flaky, cancelled, stale-target, contradictory, partial-batch, attached-run, or unexpectedly passing frontend result.

## Prime directive

Pin the exact run, preserve restricted evidence, prove target/revision with ABA defense, classify the earliest failing layer, fix one demonstrated cause, deploy the exact verified artifact, then trigger and wait a new fresh run.

```text
freeze contract -> pin run -> exact evidence -> target/revision/ABA proof
                -> classify -> fix -> exact-SHA CI -> authorized deploy
                -> prove live -> trigger new run -> wait exact ID -> terminal verdict
```

Never patch from TestSprite analysis alone. Never remove/reclassify a failed required test after execution and call that remediation.

## 1. Pin the exact run and contract

Record:

- authorized profile/account/credential endpoint, project, test, and run IDs;
- frozen plan identity/material assertions and expected `codeVersion`;
- fresh trigger, attached conflict, strict rerun, auto-healed rerun, flaky attempt, or cancellation;
- enqueue time, target origin, returned target, expected/observed release;
- terminal status/exit, failed step, request/snapshot IDs;
- batch member accounting;
- application account/role, effect, concurrency, cleanup, rollback, retention.

Preserve raw terminal JSON and run-scoped steps for every run under `umask 077` in an unpredictable temporary directory. Fetch a run artifact for failed/blocked states when available. Artifact exit 4 for cancelled/no-failure state is expected.

Do not print raw DOM, screenshots, video, forms, URLs/data, reports, generated code, or credentials into transcripts. Share only allowlisted IDs/statuses/times/versions and sanitized excerpts.

## 2. Collect exact-run evidence

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test steps "<TEST_ID>" --run-id "<RUN_ID>" --max-items 200 > "/absolute/restricted/run-dir/steps.json"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test artifact get "<RUN_ID>" --out "/absolute/restricted/run-dir/artifact"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default test code get "<TEST_ID>" --out "/absolute/restricted/run-dir/current.py"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test code get "<TEST_ID>" > "/absolute/restricted/run-dir/current-code.json"
```

`test result TEST` and `test failure get TEST` are moving latest pointers. Current code is attributable to an older run only when `codeVersion` matches. Otherwise use run-scoped source when available or mark executed source unresolved.

## 3. Reconstruct what happened

Answer:

1. Did this exact run use the authorized target and application account origin?
2. Was it newly triggered after deployment proof, or attached to an existing run?
3. Did enqueue time follow deployment proof and did returned target/`codeVersion` match the frozen contract?
4. Which version-matched generated action executed and what visible state resulted?
5. Did the plan express the frozen intended behavior?
6. Did auth, role, seed, flags, locale, viewport, tenant, or concurrency differ?
7. Did an external system/human gate prevent faithful execution?
8. Did the run reach terminal state?
9. Were all frozen batch members present and terminal?
10. Did cleanup visibly restore state?
11. Could the mutable target have changed A→B→A between equal fingerprints?

A successful click proves only an attempted action. Visible state, exact target, exact release, and preserved assertion determine the verdict.

## 4. Classify the earliest failing layer

| Class | Evidence | Fix target |
|---|---|---|
| Product | Intended release and faithful action reach app; visible contract violated | Repository code/native regression |
| Plan | Wrong intent, prerequisite, role, or assertion | Declarative plan |
| Generated code | Correct plan; wrong selector/action/timing/mechanics | Saved Python or plan refinement |
| Deployment | Old/unknown/wrong/mid-run release or target | Deploy/target/revision proof |
| Auth/environment | Wrong account, role, seed, flag, locale, tenant, configuration | Authorized environment/account |
| External gate | MFA/CAPTCHA/payment/provider/email/quota/human gate | Sandbox/operations or explicit gate |
| Runner | Failure before faithful app observation | Bounded diagnostics/vendor evidence |
| Flaky | Same plan/code/target/release/environment alternates under strict replay | Race/environment/mechanics |

Fix the earliest causally necessary failure first.

## 5. Correct responses

### Product defect

1. Add/update the repository-native regression according to policy.
2. Observe it fail first when that path is permitted.
3. Fix root cause without weakening TestSprite assertions.
4. Obtain exact-SHA CI.
5. Deploy that exact artifact with explicit authorization.
6. Prove it live before another TestSprite trigger.

### Plan defect

1. Preserve frozen required coverage; distinguish erroneous wording from contract weakening.
2. Author corrected `{ "planSteps": [...] }`.
3. Run bundled audit and vendor `test lint --steps`.
4. Use authorized optimistic `test plan put`.
5. Trigger a fresh run. A rerun can replay code generated before plan replacement.

A post-failure test removal/priority drop/reclassification is a contract change requiring explicit review, not remediation.

### Generated-code defect

1. Export current source and JSON `codeVersion` to restricted storage.
2. Make the smallest reviewed Python Playwright correction.
3. Update with `test code put --expected-version`.
4. Use strict rerun only for fast feedback when current project URL is safe/current.
5. Finish with a newly triggered fresh run on explicit target.

Never paste credentials into code.

### Deployment defect and ABA drift

Stop spending runs until the exact CI artifact is live. Prefer immutable revision URL/release. On mutable targets, require request-correlated release evidence or deployment/event evidence that excludes A→B→A drift; equal before/after fingerprints are insufficient.

### Auth/environment/external gate

Check origin-bound test account/role/tenant, seed, browser-visible login, session policy, flags, locale, viewport, region, locks, quota, parallel interference, and cleanup. Never solve auth with credential-bearing URLs or secrets in plans/code. Never bypass MFA/CAPTCHA/payment/human gates.

### Runner defect

Preserve IDs, sanitized diagnostics, CLI version/profile/target, and failure boundary. Retry only documented transient classes boundedly. Do not patch product without a faithful application observation.

## 6. Plan replacement and auto-heal

After `test plan put`, always fresh-run.

Auto-heal persistence is unresolved; do not assert it always persists or never persists. Capture saved source and `codeVersion` before/after, compare exact healed steps, then:

- if saved state already matches the reviewed intended correction, record that evidence;
- otherwise explicitly persist the reviewed plan/code correction;
- use strict replay only as feedback;
- use a new fresh trigger/wait as proof.

A healed-only green is not a release gate.

## 7. Rerun target discipline

Rerun has no `--target-url`. It uses the current project URL, not a prior fresh-run override.

Before rerun:

1. establish the current project URL through authorized state/run evidence;
2. verify application credentials remain bound to that origin;
3. ensure any project URL change is authorized, concurrency-safe, and restorable;
4. inspect returned target in rerun JSON.

If current URL cannot be established or safely changed/restored, skip rerun. Use a fresh individual run with explicit target after deployment instead.

## 8. Partial and false-green defenses

| False green | Why invalid | Correction |
|---|---|---|
| Exit 0 without wait | Dispatch only | Verify new ID/enqueue/target/version; wait exact run |
| `run_in_flight` attachment | Existing run, not new post-deploy proof | Reconcile it, then trigger a new run |
| Dry-run/lint | No browser behavior | Execute fresh trigger/wait |
| Rerun pass | Current project URL; replay, no target override | Verify target; final fresh individual run |
| Auto-heal pass | Action/state may have changed; persistence unresolved | Compare/persist correction, then fresh run |
| Flaky score | Some attempts failed | Diagnose nondeterminism |
| Cancelled | No product verdict | Correct cause and trigger fresh |
| Old/mutable target | Wrong or ABA-ambiguous release | Immutable/request-correlated proof |
| Batch create success | Creation only | Reconcile total/created/failed and IDs, then run all IDs |
| `create-batch --run --wait` | Coupled creation/execution can hide partial identity/accounting | Two-phase create, then individual runs |
| `run --all --target-url` | Rejected exit 5 | Use individual target overrides or authorized project update |
| JUnit/report exists | Can coexist with partial polling | Terminal JSON and exact run IDs |
| Assertion weakened/member removed | Contract changed | Restore frozen contract or disclose new authorization |
| Latest result green | Pointer may have moved | Exact run ID and steps |

## 9. Two-phase batch failure handling

For a frozen batch:

1. Lint every expected input individually.
2. Create without `--run`.
3. Require `failed=0`, `created=total`, and one unique test ID per input.
4. Capture the complete ID set before execution.
5. Trigger/wait each ID separately against the authorized target.
6. Preserve every terminal JSON/steps result; fetch failed/blocked artifacts.
7. Do not drop a failed member or average missing members into pass rate.

## 10. Trigger-then-wait final proof

For each frozen required test, after exact deployment proof:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test run "<TEST_ID>" --target-url "<AUTHORIZED_PUBLIC_TARGET_URL>" > "/absolute/restricted/run-dir/queued.json"
```

Require:

- new run ID not equal to any reconciled/previous run;
- enqueue time after deployment proof;
- expected target origin;
- expected `codeVersion` and frozen plan identity.

If the response reports `run_in_flight`/attachment, wait that run to terminal, preserve evidence, then trigger again. Do not use the attached run as proof.

Wait the exact new run:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test wait "<NEW_RUN_ID>" --timeout 600 > "/absolute/restricted/run-dir/terminal.json"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test steps "<TEST_ID>" --run-id "<NEW_RUN_ID>" --max-items 200 > "/absolute/restricted/run-dir/steps.json"
```

Completion requires terminal `passed`, returned target/version match, material assertions executed, frozen membership intact, same release proven with ABA defense, and cleanup complete.

## Evidence ledger

| Test/plan identity | New run/enqueue | Target/release/ABA | Expected/run code | Verdict | Classification | Restricted evidence | Cleanup/retention |
|---|---|---|---|---|---|---|---|

Allowed claims:

| Evidence | Claim |
|---|---|
| Fresh terminal pass on revision-proven target | Named contract verified on that release |
| Exact-SHA CI only | Source fix passed CI; deployment/external proof remain |
| Strict rerun pass | Saved replay passes; fresh proof remains |
| Auto-heal pass | Healed path worked; persistence/fresh proof remain |
| External gate | Happy path remains unverified |
| Runner failed before app observation | No product verdict |

## Final checklist

- Frozen required tests/plans unchanged or contract change explicitly disclosed.
- Exact new run ID/enqueue time after deployment proof.
- Attached conflicts reconciled and followed by a new trigger.
- Explicit returned target and expected `codeVersion`.
- Immutable/request-correlated ABA defense.
- Terminal JSON and steps preserved for every run.
- Failed/blocked artifact preserved when available; exit 4 handled as no artifact.
- Auto-heal source/version compared and reviewed correction persisted if needed.
- Rerun used only against verified current project URL, or skipped.
- Batch identities fully accounted for.
- Raw sensitive evidence not printed/shared without authorization.
- Cleanup, rollback, and retention completed.
- Final state is a fresh terminal pass or an explicit unverified gate.
