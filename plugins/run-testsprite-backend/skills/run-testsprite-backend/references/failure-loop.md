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
- dependency closure, `closureFailures[]`, conflicts, deferred members, and skipped members; and
- evidence correlation basis or an explicit unresolved-scope marker.

Never triage only from a dashboard screenshot or latest-test status; both can move while you work.

## 2. Collect and correlate backend evidence

Backend evidence scope is officially contradictory in 0.4.0: shipped implementation directs failures to latest `test failure get TEST_ID`, while public docs advertise run-oriented `test artifact get RUN_ID`. Do not promise an immutable backend bundle.

```bash
umask 077
EVIDENCE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/testsprite-evidence.XXXXXXXX")"
testsprite --output json test steps "$TEST_ID" \
  --run-id "$RUN_ID" --max-items 100 > "$EVIDENCE_DIR/steps.json"
testsprite --output json test result "$TEST_ID" --include-analysis > "$EVIDENCE_DIR/result.json"
testsprite --output json test failure get "$TEST_ID" --out "$EVIDENCE_DIR/failure"
testsprite test code get "$TEST_ID" --out "$EVIDENCE_DIR/failing.py"
testsprite --output json test code get "$TEST_ID" > "$EVIDENCE_DIR/code.json"
```

When installed help and actual backend output support the public artifact command, it may be attempted:

```bash
testsprite --output json test artifact get "$RUN_ID" \
  --out "$EVIDENCE_DIR/$RUN_ID-artifact"
```

Correlate each result, failure bundle, `apiOutput`, `trace`, or artifact to the pinned run ID, saved code version, explicit/observed target, request IDs, and timestamps. When backend wait uses a legacy/test-level fallback, final proof requires parseable equality `runIdIfAvailable == RUN_ID`. Missing, null, mismatched, or unparseable correlation is diagnostic-only unresolved `TestSprite execution failure`, not evidence for the pinned run.

Use `test failure summary` only for fast orientation to the latest failing run:

```bash
testsprite --output json test failure summary "$TEST_ID"
```

If exit 7 output contains a real run ID and that run is active, resume rather than retrigger. Exit 7 also covers unsupported-operation and deferred cases, so never infer a run ID:

```bash
testsprite --output json test wait "$RUN_ID" --timeout 600
```

Retrieved evidence and exported code may contain request data, user data, response tokens, or a historical embedded key. Keep them under `umask 077` in an unpredictable restricted directory. Do not print raw application payloads into transcripts; share allowlisted correlation metadata and sanitized content only.

## 3. Reconstruct the actual contract failure

Answer these from evidence:

1. Did the TestSprite Python actually execute every assertion named in the frozen ledger?
2. Which URL, method, header class, body shape, timeout, and redirect policy were used?
3. Which deployed revision answered, and what request-correlated evidence excludes mutable-target A→B→A drift?
4. Did the edge/gateway, application, provider, or TestSprite runner generate the failure?
5. Was the response syntactically valid but semantically wrong?
6. Did a producer fail before the consumer had required data?
7. Did cleanup run, and did its exact ledger assertion pass?

Read response bodies and stream events, not just status. Bound any local reproduction and use the same public hop, auth class, routing lane, and payload when those affect behavior.

## 4. Classify the failing layer

| Class | Evidence pattern | Correct fix target |
|---|---|---|
| Product code | Faithful request reaches intended revision; response violates contract | Repository implementation + native regression |
| Saved test code | Wrong URL/payload/parser/assertion, unsupported import, swallowed failure, or uncalled function | Saved TestSprite Python |
| Deployment drift | Target serves an older or unknown artifact | Deploy/prove the intended artifact; do not edit the assertion |
| Application configuration | Intended revision is live but env, binding, domain, or lane is wrong | Deployment/runtime configuration |
| Auth/account capacity | Managed credential stale, permission wrong, or no eligible account/slot exists | Credential/account operations plus typed product behavior |
| Edge/transport | CDN/gateway closes the request, TLS/DNS fails, or response never reaches application | Edge architecture/configuration or network owner |
| Provider/proxy/human gate | Upstream outage, proxy failure, CAPTCHA, SMS, payment, or quota is demonstrated | Provider/proxy operations or explicit human gate |
| TestSprite runner | Sandbox/CLI/API fails before a faithful application response | Bounded retry, CLI correction, or TestSprite support evidence |
| Dependency starvation | Producer failed or did not capture variable; consumer lacks input | Producer/capture graph, not consumer contract |
| Flaky/nondeterministic | Same code version, target fingerprint, and resource state alternate pass/fail | Product race, provider instability, or brittle assertion |

One run may expose more than one layer. Fix the earliest causally necessary failure first.

### A correct failure is still useful

If a source parser is fixed in a commit but production still serves the old revision, TestSprite should continue to fail against production. That proves the external client still sees the bug; it does not disprove the unshipped fix. Likewise, a CAPTCHA or empty account pool can correctly block a provider success case while deterministic auth/error-contract tests remain valid.

Report these states separately:

| State | Meaning |
|---|---|
| `verified` | Fresh run passed on the revision-proven target |
| `code-fixed-awaiting-deploy` | Native regression and exact-SHA CI pass; deployed target is still old or unknown |
| `runtime-gated` | Faithful run reached an account/proxy/provider/human constraint |
| `test-invalid` | Saved Python did not faithfully exercise the contract |
| `runner-unresolved` | TestSprite could not deliver a trustworthy application response |
| `product-failing` | Intended revision answered and violated the contract |

## 5. Validate the LLM hypothesis

TestSprite analysis may provide `failureKind`, `rootCauseHypothesis`, `recommendedFixTarget`, and snapshot identifiers. Turn each recommendation into a falsifiable check:

| Hypothesis | Check before editing |
|---|---|
| “Authentication token invalid” | Verify managed header was injected, target lane, response body, token freshness, and same-lane faithful probe |
| “Response schema changed” | Compare the correlated response evidence with current OpenAPI, handler, mapper, and native test |
| “Selector/step drift” | Frontend concern; for backend, inspect Python/payload and runner logs instead |
| “Timeout” | Identify who emitted it: requests client, TestSprite poll, CDN/edge, app, or upstream |
| “Missing sources” | Inspect raw JSON/SSE metadata shapes before changing the extractor |
| “Provider unavailable” | Check typed upstream evidence, capacity/account/proxy state, and retryability |

Reject a suggestion that conflicts with primary evidence. Record why; do not quietly apply a plausible patch.

## 6. Common high-value diagnoses

### Vacuous pass

Evidence: run completes immediately, no HTTP request/step evidence, function exists but is never called, or the test reaches no material assertion.

Fix:

```bash
python3 "$TESTSPRITE_SKILL_DIR/scripts/audit_backend_test.py" \
  --allowed-origin "$ALLOWED_ORIGIN" "$EVIDENCE_DIR/failing.py"
```

Resolve `TESTSPRITE_SKILL_DIR` from the loaded skill location; do not assume a target-repository path. Set `ALLOWED_ORIGIN` to the exact approved HTTPS origin when the test uses managed headers.

Call every test at module scope, restore a material assertion for each frozen ledger contract and cleanup obligation, update with `test code put --expected-version`, and run fresh. This is a test defect, not a product pass.

### Authentication 401/403

Check in order:

1. project is backend and the intended credential mode is configured;
2. test consumes `__AUTH_HEADERS__`;
3. correlated evidence shows the correct auth header *class* without exposing its value;
4. credential is current and authorized for target environment;
5. request used the same lane/tenant/host expected by the application; and
6. application auth middleware produced the body.

Do not paste a token into test code to “prove” auth. Update the managed credential through a file or fix auto-auth.

If auth is account- or lane-bound, reproduce on the same host, tenant, route, and account class. A generic token probe on another lane does not invalidate the TestSprite failure.

### Stale deployment

Evidence: correlated response data reproduces the known old behavior and the target fingerprint reports an older/unknown revision than the fixed commit.

Action: stop cloud reruns, deploy the exact CI-proven artifact, verify the live revision, then run fresh. Repeated runs against unchanged old production spend credits without adding evidence.

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

- CLI wait timeout: exit 7 with a real run ID may mean the run continues; exit 7 can also mean unsupported or deferred;
- Python `requests` timeout: test code stops waiting;
- CDN/gateway timeout such as HTTP 524: edge terminated the upstream request;
- application timeout: typed application response/log;
- provider timeout: upstream evidence and product mapping.

Increasing TestSprite's `--timeout` changes polling, not an edge's request deadline. Fix architecture, async handoff, or supported edge timeout when the response path itself exceeds the platform limit.

Treat an edge-generated 524/timeout body as a successful observation of a failed request path: the test runner worked, but the deployed architecture did not complete within the edge deadline.

### CAPTCHA, proxy, or account scarcity

Treat as an external/runtime gate when correlated TestSprite evidence and service logs prove it. Verify that product code returns the documented typed failure and does not corrupt account state. Do not weaken the success test or call the code fixed merely because native CI is green.

Retry only after observable resource state changes: a healthy account is added, a proxy is replaced, a CAPTCHA is cleared, quota resets, or provider health recovers. Time passing by itself is not evidence.

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
2. Correct the target, request, parser, timeout, or assertion without weakening or widening the frozen contract.
3. Reconcile the candidate code against the assertion ledger, including cleanup.
4. Run the static auditor with the exact `--allowed-origin` when managed headers appear.
5. Preview shape with `--dry-run`.
6. Update optimistically:

```bash
testsprite --output json test code put "$TEST_ID" \
  --code-file "$EVIDENCE_DIR/fixed.py" --expected-version "$CODE_VERSION"
```

After the update, export the final saved code and returned `codeVersion`; recheck every material and cleanup assertion in the ledger against that exact version. Reject deleted, weakened, widened, skipped, or exception-swallowed assertions.

Never change `assert sources` to `assert response.status_code == 200` just to get green.

### Environment defect

Fix the deployment, binding, target, account, or proxy through its authorized operations path. Probe the corrected environment before spending another run.

Keep deployment drift, application configuration, and runtime capacity as separate ledger entries even if the same operations team owns them. They have different proof and rollback paths.

### TestSprite transport defect

Preserve request IDs and CLI debug output after redaction. Retry only documented transient classes such as transport exit 10 or rate limit exit 11 after `Retry-After`. Validation, authentication, credit, and unresolved evidence-scope errors are not solved by looping.

### Stop an active run

Ctrl-C only detaches local polling. If the server run must stop and cancellation is authorized:

```bash
testsprite --output json test cancel "$RUN_ID"
```

`test cancel` exits 0 for cancelled/already-cancelled, 4 for not found, 6 for already-terminal conflict, and may return 1 for multi-error. A later `test wait` on the cancelled run exits 1. Cancellation does not refund credits; query final state before replacement. Exit 14 is `CLIENT_TOO_OLD`, never cancellation.

## 8. Choose replay vs fresh run

Use a backend rerun for fast feedback on the saved test and dependency closure:

```bash
testsprite --output json test rerun "$TEST_ID" --wait --timeout 600
```

Do not trust the process exit or selected-test verdict alone. Inspect every producer and teardown result plus `closureFailures[]`; any closure failure keeps the rerun non-green.

Then use a fresh run for final proof only if the test is self-contained with no dependency or teardown relationship:

```bash
testsprite --output json test run "$TEST_ID" \
  --wait --timeout 600
```

For graph-backed proof, use one fresh wave-ordered batch containing the frozen exact producer/consumer/teardown closure; require every member terminal `passed` and reject any conflict, deferred, skipped, missing, extra, or closure failure.

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

## 10. Reject partial batch success

For `test run --all`, start from the exact IDs and graph closure frozen before any run. Exit 0 is not a green verdict when the response contains `conflicts`, deferred members, skipped arrays, partial membership, queued members, or any non-passed terminal status. Require exact returned membership, empty partial-state arrays, and every accepted member terminal `passed`. Never remove a failed member or reclassify scope after execution.

A missing test is unresolved, not implicitly passed. Record each conflict/deferred/skip with its owner and next action.

## 11. Close with an evidence ledger

| Test | Run | Target/revision | Verdict | Classification | Evidence | Next state |
|---|---|---|---|---|---|---|
| source contract | run ID | URL + SHA | passed | product fixed | correlated run evidence + native regression | closed |
| provider success | run ID | URL + SHA | blocked | external account unavailable | correlated run evidence + service log | runtime gate |

Completion means every planned test is either freshly passing on the intended revision or explicitly recorded as an unresolved non-passing gate. “Four failures remain” is more accurate than averaging them into a pass rate.

A mostly passing suite can still be high-value evidence when every residual is individually understood; it is not permission to call the suite complete. Fixable product/test/deployment defects stay in the loop, while genuine account/proxy/provider gates remain named operational work.

## Anti-derailment checks

- Did the test actually call the endpoint and reach every frozen ledger assertion?
- Did the run target the intended public deployment?
- Does revision evidence match the code being judged, with A→B→A drift excluded?
- Is the failure layer proven rather than inferred from wording?
- Is a consumer merely starved by its producer?
- Did production actually receive the fix before rerunning?
- Did any account/proxy/provider state change since the last identical failure?
- Did the fix preserve the original semantic assertion in the final saved code version?
- Did cleanup complete and its assertion pass?
- Was final proof a fresh self-contained run, or a fresh exact-closure wave batch for graph-backed tests?

## Troubleshooting the loop

| Stuck state | New angle |
|---|---|
| Same patch failed twice | Rebuild request-to-response boundary evidence; stop guessing |
| Artifact and app logs disagree | Pin request ID/time/revision and check edge vs application response |
| Latest status keeps changing | Pin run ID, code version, target, request IDs, and timestamps; mark scope unresolved if latest data cannot be correlated |
| Test passes locally but not TestSprite | Compare sandbox imports, public target, managed auth, and actual Data Flow |
| Native tests pass but cloud test fails | Native proof and deployed consumer proof are different rungs; inspect runtime |
| LLM offers several fixes | Falsify each against correlated TestSprite evidence and repository code before choosing the smallest demonstrated one |
| Code fix is green but TestSprite still sees the same bug | Compare live revision first; do not patch again until the intended artifact is deployed |
| Provider test fails while deterministic tests pass | Classify resource/account/proxy evidence separately; keep the success contract intact |
