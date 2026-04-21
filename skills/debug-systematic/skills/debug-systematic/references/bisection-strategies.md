# Bisection Strategies — Narrow the Problem Space

When Phase 1's repro is not 10/10 or the failure space is too wide, bisection cuts the search surface in half at a time. Four techniques; pick by the symptom's shape.

## Decision tree — which bisection?

| Symptom | Technique | Cost |
|---|---|---|
| Fails in CI, passes locally (test pollution) | **Test-pollution bisection** — uses `scripts/find-polluter.sh` | Minutes |
| Worked last week, broken now; suspect a commit | **`git bisect run`** with a deterministic test | Minutes to hours depending on commit range |
| Broken only with feature flag X enabled | **Feature-flag toggle bisection** across N flags | Minutes |
| Intermittent with no code change; suspect input data | **Input-space bisection** — halve the input until the failure disappears | Variable |

## 1. Test-pollution bisection

**When**: a test passes alone, fails when run after other tests.

**Mechanism**: the prior tests leave shared state (in-memory cache, global singleton, module-level config, side-effecting file) that breaks the target test.

**Recipe**: use `scripts/find-polluter.sh` — the script auto-detects the test runner (jest/vitest/pytest/cargo/gotest/rspec/mvn/gradle) from the project's manifest files, then binary-searches the test list to find the smallest subset of pre-running tests that causes the target to fail.

```bash
# From the repo root
bash scripts/find-polluter.sh \
  --target "auth.test.ts > handles missing token" \
  --runner auto
```

The script outputs:
- The polluting test(s)
- The minimum reproduction command
- A suggested next action (usually: "this polluting test mutates shared X; fix with per-test setup")

### Manual equivalent (when the script isn't available)

1. List all tests that ran before the failing one in CI.
2. Binary-search: run the first half as pre-setup, then the target. If fails, the polluter is in the first half. Else it's in the second.
3. Recurse until you've narrowed to a single polluting test.

This is obra's `find-polluter.sh` approach, generalized.

## 2. `git bisect` with a deterministic script

**When**: a specific test or behavior was green at commit A, is red at commit B. Commits between may be numerous.

**Preconditions**:
- You have a deterministic test that fails on B and passes on A (usually produced by Phase 1).
- The test takes <60 seconds to run (or you have patience).

**Recipe**:

```bash
git bisect start
git bisect bad HEAD          # current commit is broken
git bisect good <commit-A>   # last-known-good commit
git bisect run bash -c '
  # build if needed
  pnpm install --frozen-lockfile && \
  # run only the failing test
  pnpm exec jest --testPathPattern=auth.test.ts --runInBand
'
```

Git checks out the middle commit, runs the script; exit 0 = good, non-zero = bad; bisects recursively.

**Output**: the first bad commit. Read its diff. The mechanism is often localized.

### Gotchas

- If your repo needs `pnpm install` between checkouts (dependency changes), include it in the script.
- If builds take minutes, narrow the commit range first by spot-checking midpoint-commits manually.
- If the script has side effects (DB migration, file writes), reset between runs.

## 3. Feature-flag toggle bisection

**When**: the failure appears only when some combination of N feature flags is enabled, and you don't know which subset.

**Mechanism**: binary search the flag set.

**Recipe**:

1. List all recently-toggled flags (N flags, 2^N combinations — do NOT enumerate all).
2. Split the flags into two halves. Enable half-A-on, half-B-off. Reproduce. Enable half-A-off, half-B-on. Reproduce.
3. Whichever half reproduces: the culprit is in there. Recurse.
4. After log2(N) rounds, you have the minimal flag set that triggers the failure.

**Example**: 16 flags toggled recently. Split into sets of 8. Group A (flags 1-8) triggers the bug; group B (flags 9-16) does not. Group A splits into 1-4 and 5-8. Group 5-8 triggers. Split 5-6 and 7-8. Group 7-8 triggers. Split 7 and 8. Flag 7 alone reproduces. Root cause: flag 7's code path.

**Tooling**: most feature-flag systems (LaunchDarkly, Unleash, in-house) support environment overrides. Use an override environment for the bisection; do not toggle in production.

## 4. Input-space bisection

**When**: the bug is intermittent, there is no clear commit or flag trigger, and you suspect the input data triggers it.

**Mechanism**: halve the input until the failure disappears. What you removed contains the trigger.

**Recipe**:

1. Capture the failing input (the payload, the user ID, the file that causes the crash).
2. Halve it: keep first half, drop second. Retry. If fails, the trigger is in the first half.
3. Recurse until the input is minimal but still fails.
4. The minimal failing input names the trigger (a specific character, field, size threshold, encoding edge case).

**Examples**:

- JSON payload: remove keys one half at a time until a minimal failing payload remains.
- File upload: halve the file size; if corruption appears at 1MB but not 512KB, the trigger is size-dependent.
- Query params: strip one half of the params; whichever half still reproduces contains the culprit.

### Coupling to Phase 1 — making an intermittent bug deterministic

Input-space bisection is often how you move from "fails sometimes" to "fails 10/10 on this specific input." Once you have the minimal failing input, the bug becomes deterministic on that input, and Phase 1's 10/10 requirement is satisfied.

## Handoff from bisection to Phase 2

Bisection narrows the problem space. It does NOT provide a mechanism on its own. The output of any bisection is one of:

- A polluting test (→ trace what shared state it mutates, that's the mechanism)
- A first-bad commit (→ read the diff, the mechanism is usually one of the changes)
- A minimal flag combination (→ trace the flag's code path, the mechanism is in the guarded code)
- A minimal failing input (→ trace what branches the input activates, the mechanism is in one of them)

Do not skip from bisection straight to Phase 4. The bisection tells you *where to look*, not *what's broken*. Phase 2 still applies.

## When NOT to bisect

- The repro is 10/10 on the current code with any input. Don't bisect — go straight to Phase 2.
- The commit range is known to be small (<5 commits) and you can read the diff directly. Reading is cheaper.
- The bug is a compile error or type error. The compiler *is* the bisection — it points at the line.
- The bug is in third-party code you cannot modify. Bisection finds the trigger, not the fix; you still need a workaround.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Running `git bisect run` with a flaky script | Make the test deterministic first; a flaky bisect produces a random commit |
| Bisecting 16 flags by trying all 65,536 combinations | Binary search; log2(N) rounds |
| Declaring the bisection result the root cause without Phase 2 tracing | Bisection narrows; it does not identify the mechanism. Continue to Phase 2. |
| Bisecting a bug that's already deterministic | Read the stack trace first; tracing is faster |
| Running bisection on a branch with broken intermediate commits | Every intermediate commit must build; otherwise the bisection lies |
