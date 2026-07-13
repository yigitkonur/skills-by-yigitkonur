# Failure Triage and Fix Loop

Use this reference after any failed, blocked, cancelled, deferred, flaky, contradictory, or unexpectedly passing TestSprite backend result.

## Prime directive

Do not patch from the LLM recommendation alone. TestSprite's analysis is a useful independent hypothesis, but the request/response record, saved code, deployed revision, repository implementation, and external dependency state decide the root cause.

Run this loop:

```text
pin run -> collect evidence -> reproduce faithfully -> classify layer
    -> fix one demonstrated cause -> native regression -> deploy exact SHA
    -> narrow replay -> fresh release run -> record residual gates
```

## 1. Pin the exact run

Capture the terminal command's JSON and exit code. Record:

- project ID;
- test ID and saved code version;
- run ID and trigger source;
- fresh run vs rerun;
- public target URL;
- expected/observed deployment revision;
- status, failure kind, failed step, and request ID; and
- dependency closure or deferred members.

Never triage only from a dashboard screenshot or latest-test status; both can move while you work.

## 2. Collect immutable evidence

```bash
mkdir -p .testsprite/runs
testsprite --output json test artifact get "$RUN_ID" \
  --out ".testsprite/runs/$RUN_ID"
testsprite --output json test steps "$TEST_ID" \
  --run-id "$RUN_ID" --max-items 100
testsprite --output json test result "$TEST_ID" --include-analysis
testsprite test code get "$TEST_ID" --out /tmp/testsprite-failing.py
testsprite --output json test code get "$TEST_ID"
```

Use `test failure summary` only for fast orientation to the latest failing run:

```bash
testsprite --output json test failure summary "$TEST_ID"
```

If the named run is still active after exit 7, resume rather than retrigger:

```bash
testsprite --output json test wait "$RUN_ID" --timeout 600
```

Artifacts and exported code may contain request data, user data, response tokens, or a historical embedded key. Store them in a gitignored restricted directory and redact before sharing.

## 3. Reconstruct the actual contract failure

Answer these from evidence:

1. Did the TestSprite Python actually execute the intended assertion?
2. Which URL, method, headers, body, and timeout were used?
3. Which deployed revision answered?
4. Did the edge/gateway, application, provider, or TestSprite runner generate the failure?
5. Was the response syntactically valid but semantically wrong?
6. Did a producer fail before the consumer had required data?
7. Did cleanup run, and was it successful?

Read response bodies and stream events, not just status. Bound any local reproduction and use the same public hop, auth class, routing lane, and payload when those affect behavior.

## 4. Classify the failing layer

| Class | Evidence pattern | Correct fix target |
|---|---|---|
| Product code | Faithful request reaches intended revision; response violates contract | Repository implementation + native regression |
| Test code | Wrong URL/payload/parser/assertion, unsupported import, or uncalled function | Saved TestSprite Python |
| Deployment/config | Old revision, missing env/binding, wrong domain, edge timeout | Deployment/runtime configuration |
| External dependency | Upstream account/proxy/CAPTCHA/outage/limit is demonstrated | Provider/account/proxy operations or typed degradation |
| TestSprite runner/transport | Sandbox/CLI/API fails before a faithful application response | TestSprite retry/support evidence |
| Dependency starvation | Producer failed or did not capture variable; consumer lacks input | Producer/capture graph, not consumer contract |
| Flaky/nondeterministic | Same saved code and target alternate pass/fail | Product race, provider instability, or overly brittle assertion |

One run may expose more than one layer. Fix the earliest causally necessary failure first.

## 5. Validate the LLM hypothesis

TestSprite analysis may provide `failureKind`, `rootCauseHypothesis`, `recommendedFixTarget`, and snapshot identifiers. Turn each recommendation into a falsifiable check:

| Hypothesis | Check before editing |
|---|---|
| “Authentication token invalid” | Verify managed header was injected, target lane, response body, token freshness, and same-lane faithful probe |
| “Response schema changed” | Compare artifact response with current OpenAPI, handler, mapper, and native test |
| “Selector/step drift” | Frontend concern; for backend, inspect Python/payload and runner logs instead |
| “Timeout” | Identify who emitted it: requests client, TestSprite poll, CDN/edge, app, or upstream |
| “Missing sources” | Inspect raw JSON/SSE metadata shapes before changing the extractor |
| “Provider unavailable” | Check typed upstream evidence, capacity/account/proxy state, and retryability |

Reject a suggestion that conflicts with primary evidence. Record why; do not quietly apply a plausible patch.

## 6. Common high-value diagnoses

### Vacuous pass

Evidence: run completes immediately, no HTTP request/step evidence, function exists but is never called.

Fix:

```bash
python3 "$TESTSPRITE_SKILL_DIR/scripts/audit_backend_test.py" /tmp/testsprite-failing.py
```

Resolve `TESTSPRITE_SKILL_DIR` from the loaded skill location; do not assume a target-repository path.

Call every test at module scope, update with `test code put --expected-version`, and run fresh. This is a test defect, not a product pass.

### Authentication 401/403

Check in order:

1. project is backend and the intended credential mode is configured;
2. test consumes `__AUTH_HEADERS__`;
3. artifact shows the correct auth header *class* without exposing its value;
4. credential is current and authorized for target environment;
5. request used the same lane/tenant/host expected by the application; and
6. application auth middleware produced the body.

Do not paste a token into test code to “prove” auth. Update the managed credential through a file or fix auto-auth.

### Missing source URLs or metadata

Inspect the raw non-stream and stream payloads. Determine whether:

- upstream omitted citations;
- app received but failed to accumulate them;
- mapper wrote a new metadata shape;
- gateway retry/stream ordering dropped them; or
- test searched the wrong field.

Add a sanitized native fixture for the observed shape. Fix the earliest parser/mapper defect. Keep the TestSprite assertion that sources are valid and non-empty if that is the product contract.

### Long-running request or edge timeout

Distinguish:

- CLI wait timeout: exit 7, run continues;
- Python `requests` timeout: test code stops waiting;
- CDN/gateway timeout such as HTTP 524: edge terminated the upstream request;
- application timeout: typed application response/log;
- provider timeout: upstream evidence and product mapping.

Increasing TestSprite's `--timeout` changes polling, not an edge's request deadline. Fix architecture, async handoff, or supported edge timeout when the response path itself exceeds the platform limit.

### CAPTCHA, proxy, or account scarcity

Treat as an external/runtime gate when the artifact and service logs prove it. Verify that product code returns the documented typed failure and does not corrupt account state. Do not weaken the success test or call the code fixed merely because native CI is green.

### Dependency starvation

If a producer in the same backend closure failed, consumers can only report missing fixtures/tokens. Triage the producer first. Rerunning a consumer with `--skip-dependencies` is valid only if you independently supply the exact required state; otherwise it changes the test.

## 7. Fix one demonstrated cause

### Product-code defect

1. Reproduce with the narrowest native test or sanitized fixture.
2. Watch the regression fail.
3. Fix the root cause without weakening the contract.
4. Run repository-required CI on the exact commit.
5. Deploy the exact verified artifact.
6. Prove the public target serves it.

### Test-code defect

1. Export current code and version.
2. Correct the target, request, parser, timeout, or assertion.
3. Run the static auditor.
4. Preview shape with `--dry-run`.
5. Update optimistically:

```bash
testsprite --output json test code put "$TEST_ID" \
  --code-file /tmp/testsprite-fixed.py --expected-version "$CODE_VERSION"
```

Never change `assert sources` to `assert response.status_code == 200` just to get green.

### Environment defect

Fix the deployment, binding, target, account, or proxy through its authorized operations path. Probe the corrected environment before spending another run.

### TestSprite transport defect

Preserve request IDs and CLI debug output after redaction. Retry only documented transient classes: transport exit 10, rate limit exit 11 after `Retry-After`, or artifact snapshot conflict after its built-in retry. Validation/auth/credit errors are not solved by looping.

## 8. Choose replay vs fresh run

Use a backend rerun for fast feedback on the saved test and dependency closure:

```bash
testsprite --output json test rerun "$TEST_ID" --wait --timeout 600
```

Then use a fresh run for final proof:

```bash
testsprite --output json test run "$TEST_ID" \
  --wait --timeout 600
```

Why both:

- rerun confirms the saved test can now execute against current state;
- fresh run provides strict new release evidence;
- backend reruns may consume credits; and
- rerun dependency side effects still occur.

## 9. Investigate flakiness deliberately

First ensure the target revision and test code version are fixed. Then:

```bash
testsprite --output json test flaky "$TEST_ID" \
  --runs 3 --until-fail --timeout 600
```

Backend attempts may consume credits and execute dependency closure. Do not run ten attempts against costly or mutable endpoints by default.

If verdicts differ, compare pinned runs:

```bash
testsprite --output json test diff "$PASS_RUN_ID" "$FAIL_RUN_ID"
```

Look for response/status/step/code-version differences, then correlate with application and provider logs. Do not “fix” flakiness by widening assertions beyond the product contract.

## 10. Close with an evidence ledger

| Test | Run | Target/revision | Verdict | Classification | Evidence | Next state |
|---|---|---|---|---|---|---|
| source contract | run ID | URL + SHA | passed | product fixed | artifact + native regression | closed |
| provider success | run ID | URL + SHA | blocked | external account unavailable | artifact + service log | runtime gate |

Completion means every planned test is either freshly passing on the intended revision or explicitly recorded as an unresolved non-passing gate. “Four failures remain” is more accurate than averaging them into a pass rate.

## Anti-derailment checks

- Did the test actually call the endpoint?
- Did the run target the intended public deployment?
- Does revision evidence match the code being judged?
- Is the failure layer proven rather than inferred from wording?
- Is a consumer merely starved by its producer?
- Did the fix preserve the original semantic assertion?
- Did cleanup complete?
- Was final proof a fresh run after deployment?

## Troubleshooting the loop

| Stuck state | New angle |
|---|---|
| Same patch failed twice | Rebuild request-to-response boundary evidence; stop guessing |
| Artifact and app logs disagree | Pin request ID/time/revision and check edge vs application response |
| Latest status keeps changing | Work only from immutable run IDs |
| Test passes locally but not TestSprite | Compare sandbox imports, public target, managed auth, and actual Data Flow |
| Native tests pass but cloud test fails | Native proof and deployed consumer proof are different rungs; inspect runtime |
| LLM offers several fixes | Falsify each against artifact/code before choosing the smallest demonstrated one |
