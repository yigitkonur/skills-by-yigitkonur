# Security, CI, and Release Proof

Use this reference for TestSprite API-key handling, managed application credentials, sensitive backend evidence, production-safe execution, CI integration, exact-revision deployment proof, cancellation, and the final release gate.

## Two credential planes

Do not confuse them:

| Credential | Purpose | Safe source |
|---|---|---|
| TestSprite API key | Lets CLI/CI call TestSprite | Inherited `TESTSPRITE_API_KEY` secret, or explicitly authorized persisted profile |
| Application credential | Lets TestSprite backend code call the tested API | TestSprite project credential or auto-auth |

Neither belongs in saved Python, repository files, CI logs, command arguments, screenshots, or shared evidence.

Managed storage removes a secret from current test source; it does not erase historical copies. If an older saved version, result bundle, shell command, or CI log contained a real key, removal plus authorized rotation is the completion condition.

## TestSprite API-key handling

Before sending a key, reject inherited `TESTSPRITE_API_URL` or explicit `--endpoint-url` unless the authorization record names that exact TLS TestSprite endpoint and confirms the selected credential belongs to its environment. These are credential-routing controls; check presence without printing values.

Prefer an inherited environment secret:

```bash
testsprite --output json auth status
testsprite --output json doctor
```

Never automatically create `.env`/`.envrc`, run `setup`, or copy the key into a command. `setup --from-env` persists the environment key and is therefore not a safe preflight. If persistent setup is explicitly authorized, use the credential-only interactive path:

```bash
testsprite setup --no-agent
```

Released 0.4.0 wrappers ignore `TESTSPRITE_PROFILE`. `TESTSPRITE_API_KEY` overrides a stored profile even when `--profile NAME` is explicit. To use a profile key, unset the inherited key on every invocation, pass the profile, and verify `auth status` identity/scopes before any write or run.

## Managed application authentication

### Static credential

Use an existing protected file created through the repository's secret manager or an authorized local process:

```bash
chmod 600 "$CREDENTIAL_FILE"
testsprite --output json project credential "$PROJECT_ID" \
  --type "Bearer token" --credential-file "$CREDENTIAL_FILE"
```

Substitute the actual supported auth type only when it matches the application. For a public API:

```bash
testsprite --output json project credential "$PROJECT_ID" --type public
```

Delete temporary credential files through the repository's approved process after successful configuration. Do not print, `echo`, paste, or commit their contents.

### Recurring token

Inspect current requirements before configuration:

```bash
testsprite project auto-auth --help
```

Use secret-file options rather than inline secret values. Configure token extraction, login URL/method/content type, scope, injection location, and key from the real auth contract. Verify one narrow non-mutating endpoint before broad execution.

### Backend test code

Vendor-shipped skill contracts name `__AUTH_HEADERS__`, `__AUTH_CREDENTIAL__`, and `__AUTH_TYPE__`. Bind managed credentials to one explicit allowed HTTPS origin. For every managed-header request, require exact scheme, canonical host, and effective port; reject URL userinfo/query targets; and set `allow_redirects=False` unless redirects were separately authorized in the operation gate. Consume an independent copy of managed headers:

```python
response = requests.get(
    f"{BASE_URL}/v1/me",
    headers=dict(__AUTH_HEADERS__),
    timeout=(10, 60),
    allow_redirects=False,
)
```

Never access, print, serialize, or expose `__AUTH_CREDENTIAL__`. Avoid exposing `__AUTH_TYPE__` unless a narrowly reviewed non-secret branch genuinely needs it. Do not print managed headers, cookies, or complete response headers.

## Audit historical tests for leaked credentials

List and export each backend test into a restricted temporary location. Fail rather than silently auditing an empty or truncated list:

```bash
set -euo pipefail
umask 077
audit_dir="$(mktemp -d "${TMPDIR:-/tmp}/testsprite-audit.XXXXXXXX")"
chmod 700 "$audit_dir"
trap 'rm -rf "$audit_dir"' EXIT

test_list="$(
  testsprite --output json test list --project "$PROJECT_ID" \
    --type backend --max-items 10000
)"
jq --exit-status '.items | length > 0' <<<"$test_list" >/dev/null
jq --exit-status '.nextToken == null' <<<"$test_list" >/dev/null

while IFS= read -r test_id; do
  code_path="$audit_dir/$test_id.py"
  testsprite test code get "$test_id" --out "$code_path"
  python3 "$TESTSPRITE_SKILL_DIR/scripts/audit_backend_test.py" \
    --allowed-origin "$ALLOWED_ORIGIN" "$code_path"
done < <(jq --raw-output '.items[].id' <<<"$test_list")
```

Set `ALLOWED_ORIGIN` to the exact approved HTTPS origin for the audited tests. Split the inventory if tests intentionally target different origins. The auditor requires this flag whenever managed headers appear and also requires `--auth-required` for authenticated-success contracts.

Resolve `TESTSPRITE_SKILL_DIR` from the loaded skill location. The auditor's request/timeouts/import/shape checks are conservative policy and do not claim to enumerate every Python shape the vendor runner accepts.

Repeat with `--auth-required --allowed-origin "$ALLOWED_ORIGIN"` for test IDs whose contract requires authenticated success. Do not use `--auth-required` for public endpoints or intentional missing/invalid-auth tests. The auditor proves only conservative shape: it cannot prove assertion strength or cleanup coverage, so retain the assertion ledger.

If a real key appeared in a saved test or evidence surface:

1. restrict old versions and bundles;
2. identify the issuing system;
3. obtain authorization for rotation;
4. create a replacement through the provider's supported path;
5. update the TestSprite project through a protected file;
6. verify one authenticated test;
7. revoke the old key; and
8. re-audit saved code and logs.

## Backend evidence handling

The backend evidence surface is officially contradictory:

- shipped implementation directs failures to latest `test failure get TEST_ID`;
- public documentation advertises run-oriented `test artifact get RUN_ID`.

Do not label backend bundles immutable by default. Set `umask 077`, create an unpredictable restricted directory with `mktemp -d`, and capture result/step/code/trace/failure/artifact output there rather than printing raw application payloads into transcripts. Correlate each item to the pinned run using run ID, saved code version, explicit/observed target, request IDs, and timestamps. If backend wait uses legacy/test-level fallback, final proof requires parseable equality `runIdIfAvailable == RUN_ID`; absent, null, mismatched, or unparseable correlation is diagnostic-only unresolved `TestSprite execution failure`. Include `apiOutput` and `trace` only inside the restricted evidence set and treat them as sensitive.

Suggested ignore entries:

```gitignore
.testsprite/runs/
testsprite-junit.xml
```

Before sharing evidence:

- remove Authorization/Cookie values;
- remove tokens, passwords, proxy credentials, and session material;
- minimize personal/request data;
- preserve correlation fields, status, timestamps, schema shape, and relevant error type; and
- state what was redacted and whether run scope was proven.

Do not commit raw production output as a regression fixture. Build a minimal sanitized fixture that preserves parser shape.

## Fail-closed operation authorization

Read-only discovery is the default. Before any TestSprite/application remote write, billable run, credential operation, test create/update/code/metadata/cancel, deployment, or application side effect, require one explicit record naming project/test IDs, exact target, TestSprite account/tenant, application account/tenant, effect, client polling and server concurrency plan, cleanup assertion/owner, and rollback/recovery. Fail closed on an omitted field or scope change; prior access or a generated plan is not authorization.

## Production-safety gate

Classify every test:

| Class | Default execution |
|---|---|
| Read-only, cheap, deterministic | Safe for ordinary fresh runs |
| Invalid-input/auth negative | Safe when bounded to one request |
| Creates reversible fixture | Isolated tenant with verified cleanup |
| Sends email/webhook/notification | Sink/fake recipient and explicit scope |
| Charges money or consumes scarce quota | Manual/filter gate and billing check |
| Deletes/changes real data | Explicit authorization and rollback required |
| High concurrency/load/fuzzing | Outside this skill |

One request to “test the API” does not authorize destructive production effects. Prefer staging, preview, or canary. If production is the only faithful target, keep probes minimal and observable.

## Exact-revision release proof

TestSprite proves the target it contacted, not the checkout on disk:

```text
commit -> exact-revision native CI -> deploy same artifact -> target revision probe
      -> fresh TestSprite test run -> target revision re-probe -> evidence ledger
```

Acceptable revision evidence includes:

- version endpoint or response header with a unique commit SHA;
- immutable image digest mapped to a commit;
- deployment API reporting source revision and artifact;
- CI provenance for the exact uploaded artifact; or
- platform release record plus live instance identity.

An older green CI run, queued deployment, branch name, or unverified URL is insufficient. Equal revision probes before and after a run are also insufficient on a mutable target because A→B→A drift can occur between probes. Require an immutable revision URL/release, or request-correlated application and deployment evidence proving the pinned TestSprite requests reached the intended revision and excluding mid-run drift.

| Plane | Question | Evidence |
|---|---|---|
| Source/native | Did the repository fix pass its own checks? | Exact-revision CI and native regression |
| Deployment | Is that artifact serving the target? | Live revision/image/release fingerprint |
| External contract | Did an independent client observe the behavior? | Fresh TestSprite run with correlated target/evidence |
| Resource health | Were accounts/proxies/providers/human gates available? | Runtime health/log/operations evidence |

One plane cannot stand in for another.

Before and after the TestSprite run, use the repository's real revision proof:

```bash
curl --fail-with-body --silent --show-error "$API_BASE_URL/version"
testsprite --output json auth status
```

`usage` may be called for information, but Portal Billing remains authoritative unless balance fields are actually returned.

## Target proof

Released 0.4.0 sources conflict over backend target semantics. Use explicit reviewed `BASE_URL` in saved Python. Do not rely on `--target-url` or teach `TARGET_URL` as guaranteed. Correlate the observed host from TestSprite output and application logs.

For public targets, MCP is optional. For localhost-only targets, use TestSprite's documented MCP route. `testsprite agent install --target ...` installs local guidance and is not MCP.

## Fresh run versus other activity

| Operation | Use | Final release proof? |
|---|---|---|
| `test rerun TEST` | Feedback on saved code and dependency closure | No |
| `test run TEST` | Fresh execution against saved backend target | Only for a self-contained test with no dependency/teardown relationship |
| `test run --all --project` | Fresh wave-ordered batch | Graph proof only with frozen exact producer/consumer/teardown closure and every member passed |
| `test flaky TEST` | Diagnose nondeterminism | No |
| `--dry-run` | Validate CLI shape | Never |
| queued/deferred/auto-attached run | Incomplete execution state | Never |

Final proof requires a fresh `test run` after deployment, an unchanged semantic contract, the final saved-code version reconciled to the assertion ledger, a revision-proven target, and correlated evidence. Individual final proof is limited to a self-contained test with no dependency/teardown relationship. Graph-backed proof requires one fresh wave-ordered batch containing the frozen exact producer/consumer/teardown closure with every member terminal `passed`.

## Batch and closure proof

Before any run, freeze exact expected test IDs, producer/consumer/teardown closure, assertions, and cleanup obligations. Do not remove a failed member or reclassify scope after execution. For a batch, exit 0 is not enough. Require:

- exact returned membership;
- no conflicts;
- no deferred or skipped arrays;
- no missing or unexpected IDs; and
- every accepted member terminal `passed`.

For backend reruns, inspect the complete producer/consumer/teardown closure and `closureFailures[]`. A selected test pass cannot hide a failed producer or teardown.

## Cancellation

Ctrl-C detaches local polling. To stop server execution when authorized:

```bash
testsprite --output json test cancel "$RUN_ID"
```

`test cancel` exits 0 for cancelled/already-cancelled, 4 for not found, 6 for already-terminal conflict, and may return 1 for multi-error. A later `test wait` on the cancelled run exits 1. Cancellation does not refund credits; query final server state before replacement. Exit 14 is `CLIENT_TOO_OLD`, never cancellation.

## CI integration pattern

Use a separate least-privilege TestSprite API key in CI. Inject it as `TESTSPRITE_API_KEY`; do not persist a profile. Treat the project ID and target URL as explicit workflow variables, not CLI defaults.

Not every test belongs in an unconditional gate:

| Suite class | CI policy |
|---|---|
| Deterministic, read-only, controlled auth | Required after deployment proof |
| Reversible isolated mutation | Gate with cleanup and bounded concurrency |
| Scarce account/proxy/provider capacity | Operational canary or provisioned gate |
| CAPTCHA/SMS/payment/human action | Manual gate; never fake green |
| Load/security/destructive behavior | Separate authorized workflow |

Example GitHub Actions shape; adapt revision extraction and explicit test IDs to the repository:

```yaml
jobs:
  testsprite-backend:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    env:
      TESTSPRITE_API_KEY: ${{ secrets.TESTSPRITE_API_KEY }}
      TESTSPRITE_PROJECT_ID: ${{ vars.TESTSPRITE_PROJECT_ID }}
      TESTSPRITE_TEST_IDS: ${{ vars.TESTSPRITE_BACKEND_TEST_IDS }}
      API_BASE_URL: ${{ vars.TESTSPRITE_IMMUTABLE_RELEASE_URL }}
      EXPECTED_REVISION: ${{ github.sha }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "22.13.0"

      - name: Install pinned TestSprite CLI
        run: npm install --global @testsprite/testsprite-cli@0.4.0

      - name: Verify TestSprite identity
        run: testsprite --output json auth status

      - name: Verify exact deployed revision before tests
        run: |
          actual_revision="$(
            curl --fail-with-body --silent --show-error "$API_BASE_URL/version" |
              jq --exit-status --raw-output '.rev | select(type == "string" and length > 0)'
          )"
          test "$actual_revision" = "$EXPECTED_REVISION"

      - name: Run explicit safe backend tests
        run: |
          set -euo pipefail
          test -n "$TESTSPRITE_TEST_IDS"
          for test_id in $TESTSPRITE_TEST_IDS; do
            result="$(testsprite --output json test run "$test_id" --wait --timeout 600)"
            jq --exit-status '
              (.runId | type == "string" and length > 0) and
              (.status == "passed")
            ' <<<"$result" >/dev/null
          done

      - name: Verify exact deployed revision after tests
        if: always()
        run: |
          actual_revision="$(
            curl --fail-with-body --silent --show-error "$API_BASE_URL/version" |
              jq --exit-status --raw-output '.rev | select(type == "string" and length > 0)'
          )"
          test "$actual_revision" = "$EXPECTED_REVISION"
```

Before adopting the JSON parser, inspect a real 0.4.0 response and adapt field paths without weakening these invariants: real run ID, terminal passed status, one result for every exact configured ID, and run correlation. This loop is valid final proof only when every ID is self-contained. For graph-backed tests, replace it with one fresh wave-ordered batch over the frozen exact producer/consumer/teardown closure and add fail-closed parsing for exact membership, conflicts, deferred/skipped arrays, and each terminal status.

The example deliberately uses an immutable release URL. If only a mutable alias exists, equal pre/post revision checks do not exclude A→B→A drift; add request-correlated application/deployment evidence for each pinned run before treating the gate as proof.

Important adaptations:

- Prove saved backend `BASE_URL` values match `API_BASE_URL`; a generic override cannot repair drift.
- If endpoints share state/capacity, serialize explicit IDs or split jobs.
- Run capacity-heavy tests only when deliberately provisioned.
- Do not upload raw failure bundles without approved storage and retention.
- Set a bounded workflow timeout longer than TestSprite polling.
- Use a fresh `test run`; do not substitute rerun, flaky, dry-run, queued, deferred, or auto-attached activity.

## CI exit handling

| Exit | CI behavior |
|---:|---|
| 0 | Parse terminal status and any batch/closure partial-state fields |
| 1 | Fail gate; collect correlated evidence in a controlled follow-up |
| 2 | Fail as not implemented; select a supported documented operation |
| 3 | Authentication/scope failure; do not retry unchanged |
| 5 | Parse/unknown-command/missing-argument/validation failure; correct input |
| 6 | Reattach only to a returned real active run ID; cancellation uses 6 for terminal conflict |
| 7 | Wait only if output includes a real run ID; otherwise classify unsupported/deferred |
| 10 | One bounded transport retry; preserve write idempotency |
| 11 | Honor `Retry-After` |
| 12 | Fail as insufficient credits; verify Portal Billing |
| 14 | Fail as `CLIENT_TOO_OLD`; upgrade client, never classify as cancellation |

CI must drive every triggered run to a terminal state. Dispatch is not behavior proof.

## Release gate checklist

Before claiming TestSprite completion:

- CLI is pinned to `@testsprite/testsprite-cli@0.4.0` on a supported Node version.
- API key came from inherited secret context; no automatic setup/env-file/profile persistence occurred; any profile use unset the env key and verified identity/scopes.
- No inherited `TESTSPRITE_API_URL` or explicit `--endpoint-url` bypassed exact TLS credential-routing authorization.
- The fail-closed operation record names account/tenant, project/test IDs, target, effects, concurrency, cleanup, and rollback.
- Native CI passed on the exact revision and the same artifact was deployed.
- Public target used an immutable release URL or request-correlated deployment/app evidence excluding A→B→A drift; localhost used the documented MCP route.
- Saved Python uses reviewed explicit `BASE_URL`; observed target correlation agrees.
- Managed application credentials were origin-bound; redirects were disabled unless separately authorized; no secret literal is present.
- Assertion ledger maps every material contract and cleanup obligation to exact assertions in the final saved code version.
- One narrow test passed before broad execution.
- Every triggered run reached terminal state or was explicitly cancelled.
- Batch membership, conflicts, deferred/skipped arrays, and terminal states were checked.
- Rerun closure members and `closureFailures[]` were checked.
- Backend evidence was run-correlated; legacy fallback had `runIdIfAvailable == RUN_ID`, otherwise it is unresolved `TestSprite execution failure`.
- Final evidence is an individual fresh run only for a self-contained test, or one fresh exact-closure wave batch for graph-backed proof.
- Every remaining account/proxy/provider/runtime gate is explicit.

## Completion report template

```text
Repository revision: revision and exact CI evidence
Deployment: target, artifact, revision proof before/after
TestSprite CLI: 0.4.0 and explicit profile only if used
Project/tests: project ID plus exact test IDs
Target proof: saved BASE_URL and observed host correlation
Fresh runs: test ID -> run ID -> terminal verdict
Batch/closure: exact membership, no partial states, closureFailures checked
Assertions: ledger mapped to exact final saved-code version; cleanup asserted
Evidence: correlation basis; legacy runIdIfAvailable equality or unresolved execution failure
Residual gates: each external/runtime failure separately
Credential audit: inherited API key; managed app auth; rotation status if needed
```

## Troubleshooting release proof

| Symptom | Response |
|---|---|
| CI green but TestSprite sees old behavior | Prove live revision before another code patch or run |
| Key vanished from source but existed historically | Rotate with authorization; restrict old output |
| Batch exited 0 with missing/skipped IDs | Keep gate red; require exact membership |
| Rerun selected test passed but producer failed | Keep gate red; inspect closure and producer evidence |
| Ctrl-C left run active | Query and explicitly cancel if authorized; parse 0/4/6/1, then note wait on cancelled exits 1 |
| Exit 14 appeared | Upgrade the client; `CLIENT_TOO_OLD` is not cancellation |
| Failure bundle may be latest rather than pinned | Correlate run/code/target/time or report unresolved |
| Usage has no balance | Portal Billing is authoritative |
| CLI upgrade changes output | Pin 0.4.0 until the workflow and parser are deliberately updated |
