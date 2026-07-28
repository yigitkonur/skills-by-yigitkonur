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

### Profile per file and per test before sharding

Suite totals hide the actual bottleneck. Because Vitest and Jest distribute by **file**, a single slow file caps the whole project no matter how many workers you add — raising concurrency cannot split one file.

Get per-file durations from the runner's own reporter output before touching sharding:

```
✓ src/services/scheduler.test.ts (155 tests) 72054ms   ← 72 s
  Test Files  100 passed (100)
  Duration    75.70s                                    ← one file is 95% of the run
```

Then read the slowest individual tests. **Suspiciously round durations are the tell.** Tests taking 8,048 / 8,037 / 24,063 ms are usually not "slow tests"; they are `n × 8000 ms` of real sleeping or backoff.

#### Real sleeps in production code are the usual culprit

The wait is frequently not in the test — it is a retry/backoff/poll delay in the code under test:

```ts
const RETRY_DELAY_MS = 8_000;
await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
```

Every test that exercises that path burns 8 seconds of wall-clock. Ranked fixes:

1. **Make the delay injectable and lower it in the test environment.** Smallest change, keeps attempt count, ordering, and guard conditions identical.
2. **Fake timers**, when the runtime supports them. Riskier: the test proves less about real scheduling.
3. **Split the file**, only if the cost is spread across many tests rather than concentrated in a few sleeps.

Measured example: injecting the delay took one file from 72.05s → 9.66s and the project from 75.70s → 14.83s (5.1×), with the test count *rising* 1866 → 1868. Verify that last part — a speedup that reduces the number of executed tests is a coverage regression wearing a stopwatch.

Do not shard a suite whose cost is concentrated in dead waiting. You would pay setup N times to parallelize sleep.

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
