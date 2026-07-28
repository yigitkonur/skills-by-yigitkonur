# Testing and Flakiness

Use this file when test execution dominates the critical path, when retries or
re-runs inflate wall-clock, or when a green run still leaves doubt about whether
the failure was real.

Read `measurement.md` first if the slowdown has not been separated into queue vs
execution. Read `feedback-loops.md` when the question is how to learn the result
without blocking.

## Sharding principles

- Split the suite so every required test runs exactly once.
- Prefer historical-duration balancing over raw file-count splitting.
- Keep test isolation; shared databases, ports, files, and global state force serial lanes.
- Increase shard count only while p95 wall-clock improves. Setup/reporting is the serial tail.
- Merge results and coverage in a fan-in job; gate on the merged result.

If the first shard plan that looks parallel also adds a heavy planner job or
several short setup-heavy lanes, price the hop first in `capacity-and-contention.md`.

## Playwright

```bash
npx playwright test --shard=${SHARD_INDEX}/${SHARD_COUNT} --reporter=blob
npx playwright merge-reports --reporter=html ./all-blob-reports
```

Use `fullyParallel: true` only when tests are isolated enough for test-level
distribution. Upload each shard's blob report and merge them.

## Vitest

```bash
vitest run --reporter=blob --shard=${SHARD_INDEX}/${SHARD_COUNT}
vitest run --merge-reports
```

Vitest distributes by test file by default. A few large files can still dominate;
split large files or use provider timing-aware splitting.

## Jest

Jest `--shard` balances by file count unless a custom sequencer uses historical
timings. CircleCI and similar providers can split by JUnit timing metadata:

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

Retries are a detection and temporary-confidence mechanism. A retry-pass is still
evidence of instability. Track flake rate, rerun count, owner, and age.

## Re-run the identical commit before changing code

If a red check appears on a commit whose diff does not plausibly reach the failing
test, re-run the **identical commit** before touching code. A pass on the
unchanged tree demonstrates flakiness or infrastructure drift, not a fixed bug.

That is the reliable test. Provider flake counters are useful priors, not proof:
they often only count a step that eventually succeeded, so a
failing-then-passing test can still read as zero flakes.

Do **not** “fix” a flake by:

- widening a threshold,
- adding an unconditional retry,
- skipping the test,
- mocking the failure away,
- rerunning until green and calling it solved.

Those weaken the measurement instead of fixing the pipeline. Cross-link:
`effectiveness-contract.md`.

## Coverage

- Choose one coverage engine per suite; do not mix V8 and Istanbul artifacts across shards.
- Upload per-shard coverage and merge deliberately.
- Disable coverage on the PR critical path only if coverage is not a required merge gate; otherwise shard or optimize it.

## Failure behavior

- Use fail-fast between serial stages when downstream cannot succeed.
- Avoid cancelling every matrix shard on the first failure when full shard signal helps diagnose systemic issues.
- Preserve JUnit/blob/report artifacts on failure.

## Cross-links

- `feedback-loops.md` — how to surface the first failing lane without blocking.
- `capacity-and-contention.md` — when sharding neutralizes or worsens wall-clock.
- `measurement.md` — how to compare sharded and unsharded runs honestly.
- `integration-environments.md` — when the flake is shared state, ports, or services rather than test logic.
- `effectiveness-contract.md` — why retries and skips are not optimization.

## Sources

- Playwright sharding: https://playwright.dev/docs/test-sharding (accessed 2026-07-28)
- Vitest performance/reporters/coverage: https://vitest.dev/guide/improving-performance ; https://vitest.dev/guide/reporters ; https://vitest.dev/guide/coverage (accessed 2026-07-28)
- Jest CLI: https://jestjs.io/docs/cli (accessed 2026-07-28)
- CircleCI test splitting: https://circleci.com/docs/guides/optimize/parallelism-faster-jobs/ (accessed 2026-07-28)
- Google flaky tests: https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html (accessed 2026-07-28)
- Mergify flaky guidance: https://mergify.com/learn/flaky-tests/playwright (accessed 2026-07-28)
