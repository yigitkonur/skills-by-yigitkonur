# Repository Discovery and Public Target Proof

Read this before creating/running frontend tests in an unfamiliar repository, choosing TestSprite state, supplying application credentials, or claiming a deployed revision was verified.

## Discovery brief

Complete before a cloud run:

| Question | Evidence | Decision |
|---|---|---|
| User journey and material contract | Product docs, routes/pages, maintained native tests | Frozen plan/test identity |
| Existing TestSprite state | Project/test/history/code/run evidence | Reuse/update/create |
| Faithful target | Deploy policy and environment controls | Exact authorized origin |
| Live revision | Immutable URL/release, deployment API, digest, request correlation | Expected and observed identity |
| Account and credentials | Auth/fixture docs and secret mechanism | Authorized role, origin binding |
| Side effects | Journey/integration trace | Effect, concurrency, cleanup, rollback |
| External gates | MFA/CAPTCHA/provider/email/payment/quota | Preflight or explicit gate |
| Evidence handling | Data classification and retention policy | Restricted path/share/delete plan |

Do not fill load-bearing unknowns with guesses.

## 1. Read repository authority

Find root and scoped instructions, then record branch/worktree rules, generated files, CI-only testing, secret handling, production/browser policy, deployment authorization, revision proof, and ignored runtime artifacts.

Map routes/pages, forms, auth guards, roles, responsive/accessibility-visible contracts, native Playwright/Cypress tests, fixtures, cleanup helpers, deployment workflow, and revision surfaces. Trace one journey:

```text
entry origin -> auth boundary -> user action -> state transition
             -> visible outcome -> persistence -> cleanup
```

Repository policy outranks generic examples in this skill.

## 2. Rank conflicting evidence

Use:

1. observed behavior on the intended revision;
2. executable application code and maintained native tests;
3. product/accessibility/design contracts;
4. maintained user documentation;
5. comments, old screenshots, examples, generated prose.

Do not weaken the easiest assertion. Correct stale deployment before diagnosing product/test behavior there.

## 3. Credential-routing preflight

Treat all endpoint controls as security boundaries:

- inherited `TESTSPRITE_API_URL`;
- CLI `--endpoint-url`;
- MCP `API_URL`;
- tunnel endpoint/host overrides.

Reject inherited/custom routing by default. Authorize only an exact TLS endpoint with the matching TestSprite credential environment. Never send production credentials to a staging/custom endpoint or allow an unreviewed redirect.

An inherited `TESTSPRITE_API_KEY` overrides a selected stored profile key. If using stored profile credentials deliberately, unset the inherited key for that command and verify identity/scopes before any write/run.

Bind application login/project credentials to the exact authorized target origin. Never use userinfo in a target URL. Do not carry credentials across an origin change, even when project/test IDs remain the same.

## 4. Inspect existing TestSprite state

Every network invocation is self-contained, pinned, and uses a concrete profile:

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json project list --max-items 100
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json project get "<PROJECT_ID>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test list --project "<PROJECT_ID>" --type frontend --max-items 200
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test get "<TEST_ID>"
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json test result "<TEST_ID>" --history --since 7d
```

For generated source, write to a restricted unpredictable temporary directory and capture JSON `codeVersion`; do not print source to transcripts.

Record project/test IDs and types, recent exact run IDs/targets/verdicts, current code version, intended journey, account/role/seed assumptions, side effects, concurrency, cleanup, and current plan identity. Reuse only when the material contract matches.

Freeze all required release-gating test IDs and plan identities before execution. A post-failure removal/reclassification is a contract change.

## 5. Project URL caveat

Project list/get does not reliably expose the stored URL. Prefer individual fresh runs with explicit `--target-url`.

Before `project update`, require explicit authorization and either:

- a dedicated project with no conflicting active users/runs; or
- independently known prior URL, concurrency safety, credential-origin revalidation, and authorized restoration/rollback.

```bash
npm exec --yes --package=@testsprite/testsprite-cli@0.4.0 -- testsprite --profile default --output json project update "<PROJECT_ID>" --url "<AUTHORIZED_PUBLIC_TARGET_URL>"
```

Verify returned target from a completed run and restore prior state when required. If safe change/restoration is impossible, skip rerun and `--all`; use individual fresh runs.

Rerun always uses the current project URL. It never inherits an earlier fresh-run target override. Verify its returned target before interpreting it.

## 6. Select a safe target

Prefer:

1. immutable preview/canary URL for exact revision;
2. staging with production-equivalent behavior and controlled accounts;
3. production only when necessary and explicitly scoped.

The CLI rejects localhost/private IP/private hostnames. Use the fail-closed MCP reference for private-only work.

Before a browser mutation, answer:

- exact target origin and account/tenant/role;
- create/update/delete/outward effects;
- email/webhook/notification/invitation/public content;
- uploads/downloads and sensitive data;
- money, inventory, quota, or scarce providers;
- parallel-run races;
- deterministic cleanup and rollback;
- evidence retention.

If unsafe/unknown, redesign to read-only or negative validation, use an authorized sandbox/sink, or preserve an explicit gate.

## 7. Prove public reachability and revision

Use repository-native health/revision evidence; do not invent `/version`.

Strong proof:

- immutable revision URL or immutable release identity;
- live full SHA/digest/release ID mapped to exact CI artifact;
- deployment API plus request-correlated backend/release logs;
- signed/build metadata exposed by the live application.

### ABA defense

A pre-run fingerprint of A and post-run fingerprint of A does not prove stability: the target may have changed A→B→A during the run.

Use one of:

1. immutable revision-specific URL/release;
2. infrastructure guarantee that the release cannot change during the bounded run, with evidence;
3. request-correlated evidence for the TestSprite run window showing every served request resolved to the same release/digest;
4. deployment/event logs proving no intervening release transition.

If none is available, report weaker revision evidence and do not claim exact-release proof.

Record immediately before trigger and after terminal wait:

| Field | Required value |
|---|---|
| Target | Exact public origin/base path |
| Environment | Preview/staging/canary/production |
| Release | Full SHA/digest/immutable release ID |
| ABA defense | Immutable URL or request/deployment correlation |
| Lane | Tenant/region/flags/account role |
| Test | Frozen test ID/plan identity/expected codeVersion |
| Runtime | Profile/account/external dependencies |
| Time | Deployment proof, enqueue time, terminal time |

## 8. Convert discovery into the execution manifest

For every frozen test record priority, plan identity, test ID, journey, visible assertion, target, expected codeVersion, mutation/effect, account/gate, concurrency, cleanup, rollback, and retention.

Run only the complete manifest. Do not omit a failed test, relabel it optional, or replace its assertion after execution without declaring and authorizing a new contract.

## Troubleshooting

| Symptom | Response |
|---|---|
| Several projects match | Compare types, tests, histories, targets; do not guess |
| Stored URL unknown | Use individual fresh target override; avoid shared mutation |
| Target works locally but CLI rejects it | It is private; use authorized disposable MCP or public deploy |
| Fixed code shows old behavior | Prove live release before another code/test patch |
| Before/after release matches but drift possible | Add immutable/request-correlated ABA evidence |
| Auth works manually only | Match origin, account, role, seed, and cloud-browser login path |
| Rerun reaches old target | Rerun uses current project URL; safely update/verify or skip it |
| MFA/CAPTCHA/payment blocks | Use authorized sandbox path or retain external gate |
