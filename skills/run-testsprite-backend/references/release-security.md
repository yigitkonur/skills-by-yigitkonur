# Security, CI, and Release Proof

Use this reference for managed credentials, sensitive artifacts, production-safe execution, CI integration, exact-revision deployment evidence, and the final TestSprite release gate.

## Two credential planes

Do not confuse them:

| Credential | Purpose | Storage |
|---|---|---|
| TestSprite API key | Lets CLI/CI call TestSprite | `~/.testsprite/credentials` profile or `TESTSPRITE_API_KEY` CI secret |
| Application credential | Lets TestSprite backend code call the tested API | TestSprite project credential or auto-auth |

Neither belongs in saved Python, repository files, CI logs, command-line arguments, screenshots, or shared artifacts.

## Managed application authentication

### Static bearer/API/basic credential

Use an existing protected file created through the repository's secret manager or authorized local process:

```bash
chmod 600 "$CREDENTIAL_FILE"
testsprite --output json project credential "$PROJECT_ID" \
  --type "Bearer token" --credential-file "$CREDENTIAL_FILE"
```

Substitute `API key` or `basic token` only when that is the API's actual auth scheme. For a public API:

```bash
testsprite --output json project credential "$PROJECT_ID" --type public
```

Delete temporary credential files after the command succeeds using the repository's approved secret-handling process. Do not print, `echo`, paste, or commit their contents.

### Recurring token

TestSprite 0.3.0 Pro supports `password`, `refresh_token`, and `aws_cognito_refresh` methods. Inspect exact requirements:

```bash
testsprite project auto-auth --help
```

Use secret file options:

- `--password-file`;
- `--client-secret-file`; and
- `--refresh-token-file`.

Avoid inline secret flags. Configure token JSONPath, login URL/method/content type, scope, injection location, and key from the real auth contract. Test auto-auth with one narrow non-mutating endpoint before a broad suite.

### Test code

Consume only managed headers:

```python
response = requests.get(
    f"{BASE_URL}/v1/me",
    headers=dict(__AUTH_HEADERS__),
    timeout=(10, 60),
)
```

Do not print `__AUTH_HEADERS__`, `__AUTH_CREDENTIAL__`, cookies, or entire response headers.

## Audit historical tests for leaked credentials

List and export each backend test into a restricted temporary location:

```bash
testsprite --output json test list --project "$PROJECT_ID" \
  --type backend --max-items 100
testsprite test code get "$TEST_ID" --out /tmp/testsprite-audit.py
python3 "$TESTSPRITE_SKILL_DIR/scripts/audit_backend_test.py" \
  --auth-required /tmp/testsprite-audit.py
```

Resolve `TESTSPRITE_SKILL_DIR` from the loaded skill location rather than the target repository.

The auditor reports a likely secret without printing it. Also inspect TestSprite-managed failure bundles, shell history, CI logs, and committed history when exposure is suspected.

If a real key appeared in a saved test or artifact:

1. treat the old test versions/artifacts as sensitive;
2. identify the provider/system that issued the key;
3. obtain authorization for credential rotation;
4. create a replacement through the provider's supported path;
5. update TestSprite with the replacement through a file;
6. verify one authenticated test;
7. revoke the old key; and
8. re-audit saved code and logs.

Removing the literal from current code is necessary but does not invalidate copies already stored elsewhere.

## Artifact handling

Add TestSprite local outputs to repository ignore rules when they are not already covered:

```gitignore
.testsprite/runs/
testsprite-junit.xml
```

Before sharing an artifact:

- remove Authorization/Cookie values;
- remove tokens, passwords, proxy credentials, and TOTP/session material;
- minimize personal/request data;
- preserve run ID, request ID, status, timestamps, schema shape, and relevant error type; and
- say what was redacted.

Do not commit raw production artifacts as regression fixtures. Build a minimal sanitized fixture that preserves the parser shape.

## Production-safety gate

Classify every test:

| Class | Default execution |
|---|---|
| Read-only, cheap, deterministic | Safe for ordinary fresh runs |
| Invalid-input/auth negative | Safe when bounded to one request |
| Creates reversible fixture | Only in isolated tenant with verified cleanup |
| Sends email/webhook/notification | Use sink/fake recipient and explicit scope |
| Charges money or consumes scarce quota | Manual/filter gate and credit check |
| Deletes/changes real data | Do not run without explicit authorization and rollback |
| High concurrency/load/fuzzing | Outside this skill; use authorized specialist workflow |

One user request to test an API does not silently authorize destructive production effects. Prefer staging/preview/canary. If production is the only faithful target, keep probes minimal and observable.

## Exact-revision release proof

TestSprite proves the deployment it contacted, not the source checkout on disk. Use this sequence:

```text
commit -> exact-SHA native CI -> deploy same artifact -> target version probe
      -> TestSprite fresh run -> target version re-probe -> evidence ledger
```

Acceptable revision evidence includes:

- `/version` or response header containing full/unique commit SHA;
- immutable image digest mapped to commit;
- deployment API reporting source revision and artifact;
- CI provenance for the exact uploaded artifact; or
- platform release record plus live instance identity.

An older green CI run, a queued deployment, or a branch name is not exact-SHA proof.

Before the TestSprite run:

```bash
curl --fail-with-body --silent --show-error "$API_BASE_URL/version"
testsprite --output json auth status
testsprite --output json usage
```

After the run, probe version again to catch a mid-run deployment change.

## Fresh run vs rerun

| Operation | Use | Final release proof? |
|---|---|---|
| `test rerun TEST` | Fast feedback on saved code/dependency closure | No |
| `test run TEST` | Strict fresh execution against URL saved in backend Python | Yes |
| `test run --all --project` | Fresh wave-ordered safe batch | Yes, if saved targets/concurrency are correct |
| `test flaky TEST` | Diagnose nondeterminism; may consume backend credits | No by itself |
| `--dry-run` | Validate CLI shape only | Never |

Do not rely on `--target-url` for any backend run; it has no effect in 0.3.0. Update saved Python with optimistic versioning or maintain environment-specific tests, then verify the run Data Flow.

## CI integration pattern

Use a separate least-privilege TestSprite API key in CI. Store the TestSprite key, project ID, target URL, and application credential in the CI secret/variable system; never commit them.

Example GitHub Actions job (adapt runner, install policy, workflow triggers, and revision probe to the repository):

```yaml
jobs:
  testsprite-backend:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    env:
      TESTSPRITE_API_KEY: ${{ secrets.TESTSPRITE_API_KEY }}
      TESTSPRITE_PROJECT_ID: ${{ vars.TESTSPRITE_PROJECT_ID }}
      API_BASE_URL: ${{ vars.TESTSPRITE_TARGET_URL }}
      EXPECTED_REVISION: ${{ github.sha }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install pinned TestSprite CLI
        run: npm install --global @testsprite/testsprite-cli@0.3.0

      - name: Verify TestSprite identity
        run: testsprite --output json auth status

      - name: Verify exact deployed revision before tests
        run: |
          actual_revision="$(
            curl --fail-with-body --silent --show-error "$API_BASE_URL/version" |
              jq --exit-status --raw-output '.rev | select(type == "string" and length > 0)'
          )"
          test "$actual_revision" = "$EXPECTED_REVISION"

      - name: Run safe P0 backend tests
        run: |
          testsprite --output json test run --all \
            --project "$TESTSPRITE_PROJECT_ID" --filter "P0" \
            --wait --timeout 600 --max-concurrency 4 \
            --report junit --report-file ./testsprite-junit.xml

      - name: Verify exact deployed revision after tests
        if: always()
        run: |
          actual_revision="$(
            curl --fail-with-body --silent --show-error "$API_BASE_URL/version" |
              jq --exit-status --raw-output '.rev | select(type == "string" and length > 0)'
          )"
          test "$actual_revision" = "$EXPECTED_REVISION"

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: testsprite-junit
          path: testsprite-junit.xml
          if-no-files-found: ignore
```

Important adaptations:

- The example assumes `/version` returns the full commit SHA in `.rev`. Adapt the extraction to the repository's revision surface, but keep exact equality against the expected SHA before and after TestSprite.
- Before the batch, prove its saved backend code targets `API_BASE_URL`; a CLI target override cannot repair drift.
- If endpoints share scarce state/capacity, serialize explicit IDs or split jobs; `--max-concurrency` is not service serialization.
- Pin or deliberately update the CLI. Run `testsprite agent status` when repository guidance is generated by the CLI.
- Do not upload raw failure bundles unless the artifact store and retention policy are approved for their data.
- Respect repository rules that prohibit schedules, production CI calls, or local builds.
- Set a workflow timeout longer than TestSprite `--timeout`, but still bounded.

## CI exit handling

| Exit | CI behavior |
|---:|---|
| 0 | Parse JSON summary; queued-without-wait is not pass |
| 1 | Fail gate; fetch pinned artifacts in a controlled follow-up |
| 3/5 | Configuration failure; do not retry |
| 6 | Reattach to returned active run rather than duplicate |
| 7 | Persist run ID and wait same run within remaining deadline |
| 10 | One bounded transport retry using same idempotency for writes |
| 11 | Honor `Retry-After`; do not busy-loop |
| 12 | Fail with insufficient-credit classification |

CI should always drive triggered runs to a terminal state. A workflow that exits after queueing measures dispatch, not behavior.

## Release gate checklist

Before claiming TestSprite completion:

- Native tests/CI passed on the exact commit.
- The exact artifact was deployed.
- Public target was healthy and revision-proven before and after runs.
- Managed credentials were used; saved code contains no secret literals.
- One narrow test passed before broad execution.
- Every triggered run reached a terminal state.
- Failures have run-scoped artifacts and a demonstrated classification.
- Dependency-starved consumers are not mislabeled as product defects.
- Capacity-heavy tests were safely serialized or filtered.
- Final evidence is a fresh run, not dry-run or rerun alone.
- Every unresolved account/proxy/provider/runtime gate remains explicit.
- Local artifacts and temporary secret files are protected or removed.

## Completion report template

```text
Repository commit: <sha>
Native CI: <run URL/status for same sha>
Deployment: <target URL, artifact/revision evidence>
TestSprite CLI: <version/profile>
Project: <id/name/type>
Fresh runs: <test id -> run id -> verdict>
Assertions: <semantic contracts proven>
Artifacts: <restricted local paths/dashboard URLs>
Residual gates: <none, or each external/runtime failure separately>
Credential audit: <managed mode; no literals found; rotation status if applicable>
```

## Troubleshooting release proof

| Symptom | Response |
|---|---|
| CI green but TestSprite still sees old bug | Target serves old artifact; deploy/prove revision before rerun |
| Secret is absent from current test but was historically stored | Rotate provider credential and treat old artifacts as sensitive |
| Batch is green on wrong environment | Update saved Python or use environment-specific tests, then verify Data Flow |
| JUnit exists but command timed out | JUnit is not terminal proof; resume run IDs |
| Provider tests remain blocked after code fix | Report separate runtime gate; do not redefine code success as live success |
| CLI upgrade changes command shape | Read installed `--help`, update pinned version/guidance, and dry-run before writes |
