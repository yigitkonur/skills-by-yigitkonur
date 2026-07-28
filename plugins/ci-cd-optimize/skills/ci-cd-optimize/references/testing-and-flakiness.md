# Testing and Flakiness

Use this file when test execution dominates the critical path or retries/reruns inflate pipeline time.

## Sharding principles

- Split the suite so every required test runs exactly once.
- Prefer historical-duration balancing over raw file-count splitting.
- Keep test isolation; shared databases, ports, files, and global state force serial lanes.
- Increase shard count only while p95 wall-clock improves. Setup/reporting is the serial tail.
- Merge results and coverage in a fan-in job; gate on the merged result.

## Playwright

```bash
npx playwright test --shard=${SHARD_INDEX}/${SHARD_COUNT} --reporter=blob
npx playwright merge-reports --reporter=html ./all-blob-reports
```

Use `fullyParallel: true` only when tests are isolated enough for test-level distribution. Upload each shard's blob report and merge them.

## Vitest

```bash
vitest run --reporter=blob --shard=${SHARD_INDEX}/${SHARD_COUNT}
vitest run --merge-reports
```

Vitest distributes by test file by default. A few large files can still dominate; split large files or use provider timing-aware splitting.

## Profile per file before sharding

File-distributing runners (Vitest, Jest) cannot split one slow file, so a
single dominant file caps the run regardless of `maxWorkers` or shard
count. Read per-file durations from the reporter first, then per-test
within the worst file.

Durations clustered at round numbers (8,048 ms, 8,037 ms, 24,063 ms =
n × 8,000 ms) are real waiting — usually a retry/backoff/poll delay in the
*code under test*, not in the test. Ranked fixes:

1. Make the delay injectable and lower it only in the test environment,
   keeping the production value as the default — behavior provably
   unchanged.
2. Fake timers — proves less, and sandboxed runtimes handle them poorly.
3. Split the file — only if the cost is actually spread across tests.

Measured: one file 72.05 s → 9.66 s, project 75.70 s → 14.83 s (5.1×),
with the executed-test count *rising* 1,866 → 1,868. Always verify the
count did not fall — a speedup that drops executed tests is a coverage
regression, not an optimization. Corollary: never shard a suite whose cost
is concentrated in dead waiting; that pays setup N times to parallelize
sleep.

## Jest

Jest `--shard` balances by file count unless a custom sequencer uses historical timings. CircleCI and similar providers can split by JUnit timing metadata:

```bash
npx jest --listTests | circleci tests run \
  --command="JEST_JUNIT_ADD_FILE_ATTRIBUTE=true xargs npx jest --runInBand --" \
  --split-by=timings
```

## Flaky-test policy

| State | Action |
|---|---|
| Unknown intermittent failure | Reproduce, capture logs/artifacts, classify cause. |
| Active flake being fixed | Bounded retry or quarantine with owner and deadline. |
| Recovered test | Automatic re-entry into the blocking suite. |
| Chronic flake | Fix infrastructure/test design or remove from required path with explicit risk acceptance. |

Retries are a detection and temporary-confidence mechanism. A retry-pass is still evidence of instability. Track flake rate, rerun count, owner, and age.

Interpretation rules:

- A pass on rerun is **not** a clean green. It means the run was unstable and
  still consumed time and trust.
- Re-run the **same commit** when classifying a suspected flake; changing the
  commit at the same time destroys the diagnosis.
- Blanket suite retries are a last resort and should be reported as a
  mitigation, not as a fix.
- Preserve the first failing artifacts and logs even if later attempts pass.

## Coverage

- Choose one coverage engine per suite; do not mix V8 and Istanbul artifacts across shards.
- Upload per-shard coverage and merge deliberately.
- Disable coverage on the PR critical path only if coverage is not a required merge gate; otherwise shard or optimize it.

## Failure behavior

- Use fail-fast between serial stages when downstream cannot succeed.
- Avoid cancelling every matrix shard on the first failure when the full
  shard signal helps diagnose systemic issues.
- Preserve JUnit/blob/report artifacts on failure.
- Distinguish "first red, stop the rollout" from "cancel the entire test
  matrix immediately". Full shard signal often matters more than a few
  saved minutes once failure is known.

## Sources

- Playwright sharding: https://playwright.dev/docs/test-sharding (accessed 2026-07-28)
- Vitest performance/reporters/coverage: https://vitest.dev/guide/improving-performance ; https://vitest.dev/guide/reporters ; https://vitest.dev/guide/coverage (accessed 2026-07-28)
- Jest CLI: https://jestjs.io/docs/cli (accessed 2026-07-28)
- CircleCI test splitting: https://circleci.com/docs/guides/optimize/parallelism-faster-jobs/ (accessed 2026-07-28)
- Google flaky tests: https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html (accessed 2026-07-28)
- Mergify flaky guidance: https://mergify.com/learn/flaky-tests/playwright (accessed 2026-07-28)
