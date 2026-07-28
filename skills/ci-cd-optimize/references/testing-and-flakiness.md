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

## Profile per file and per test before sharding

Suite totals hide the bottleneck. File-distributing runners (Vitest, Jest) cannot split a single slow file, so raising workers does nothing when one file is 95 % of the run. Read the runner's own per-file report first. **Durations clustered at suspiciously round numbers are the tell**: tests at 8,048 / 8,037 / 24,063 ms are `n × 8000 ms` of real waiting, and the wait is frequently a retry/backoff delay in the code under test, not in the test. Ranked fixes: (1) make the delay injectable and lower it only in the test environment — production default unchanged, attempt counts identical; (2) fake timers, accepting they prove less about real scheduling; (3) split the file, which helps only if the cost is spread. Do not shard a suite whose cost is concentrated in sleeping — that pays setup N times to parallelize `setTimeout`. Verify the test count did not fall after any speedup; fewer executed tests is a coverage regression wearing a stopwatch.

## Flake triage without weakening the test

When CI fails, decide whether it is *your* failure before changing code: diff the failing commit against the last green one, and if nothing in the diff can plausibly reach the failing test, re-run the **identical commit** rather than pushing a speculative fix. A pass on the unchanged commit demonstrates a flaky test — a separate defect to quarantine and own, never to "fix" by relaxing the assertion or retrying until green. Provider flake counters are a prior, not a substitute: the identical-commit re-run is the reliable test. (Some providers report one record per re-run *attempt*; collapse to the highest attempt per run id before judging a verdict — see `references/measurement.md`.)

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

## Coverage

- Choose one coverage engine per suite; do not mix V8 and Istanbul artifacts across shards.
- Upload per-shard coverage and merge deliberately.
- Disable coverage on the PR critical path only if coverage is not a required merge gate; otherwise shard or optimize it.

## Failure behavior

- Use fail-fast between serial stages when downstream cannot succeed.
- Avoid cancelling every matrix shard on the first failure when full shard signal helps diagnose systemic issues.
- Preserve JUnit/blob/report artifacts on failure.

## Sources

- Playwright sharding: https://playwright.dev/docs/test-sharding (accessed 2026-07-28)
- Vitest performance/reporters/coverage: https://vitest.dev/guide/improving-performance ; https://vitest.dev/guide/reporters ; https://vitest.dev/guide/coverage (accessed 2026-07-28)
- Jest CLI: https://jestjs.io/docs/cli (accessed 2026-07-28)
- CircleCI test splitting: https://circleci.com/docs/guides/optimize/parallelism-faster-jobs/ (accessed 2026-07-28)
- Google flaky tests: https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html (accessed 2026-07-28)
- Mergify flaky guidance: https://mergify.com/learn/flaky-tests/playwright (accessed 2026-07-28)
