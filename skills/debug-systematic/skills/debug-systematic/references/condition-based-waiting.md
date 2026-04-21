# Condition-Based Waiting — Polling With Timeout

Replace `sleep(n)` with a loop that polls a condition. Arbitrary delays hide races; condition-based waits either pass quickly on success or fail loudly on timeout. Language-neutral template here; drop-in code per language in `references/waiting/<lang>.md`.

## The pattern

```
fn wait_for(condition, timeout_ms, interval_ms=10):
    deadline = now() + timeout_ms
    while now() < deadline:
        if condition():                    # re-read fresh state per iteration
            return OK
        sleep(interval_ms)
    return TIMEOUT_ERROR("wait_for: <condition description>; timed out after N ms")
```

**Mandatory elements**:

1. **Fresh read per iteration.** Do not cache the condition's inputs; the whole point is that state changes.
2. **Tight interval.** 10ms default; increase only if the condition is legitimately expensive to check.
3. **Hard timeout.** Never wait forever. Every call has a deadline.
4. **Descriptive timeout error.** The error names *what* was being waited for so Phase 1 has evidence.

## Why this beats `sleep(n)`

| Issue with `sleep(n)` | Resolution |
|---|---|
| "Sometimes passes, sometimes fails" — the sleep is short enough to race | Condition-based waits are deterministic: they return as soon as the condition is true |
| Tests slow to an unnecessary floor because every `sleep(500)` takes 500ms even when the event happens in 10ms | Condition-based waits return fast on success |
| When the condition never happens, `sleep(n)` hides the failure — the assertion later produces a confusing error | Condition-based waits produce a named timeout error with context |
| Test flakiness under load — the "safe" sleep value is hardware-dependent | Condition-based waits adapt to the actual event timing |

## When NOT to poll

- **Deterministic signal available** — event hook, callback, promise, channel, future. Use the signal directly.
- **Mock-clock available** — test framework provides a fake timer; advance the clock instead of waiting.
- **The wait is for a build or compile step** — use the build tool's completion signal, not a sleep loop around file mtime.
- **The resource is reachable via a synchronous API** — call the API, don't poll.

Polling is the fallback. Prefer direct signals when they exist.

## Drop-in code by language

Each language reference contains three utility functions (`waitForEvent` / `waitForEventCount` / `waitForEventMatch`), idiomatic to the language's test framework, plus a timeout helper.

| Language | Reference |
|---|---|
| TypeScript / Jest / Vitest | `references/waiting/typescript.md` |
| Python / pytest | `references/waiting/python.md` |
| Rust / tokio | `references/waiting/rust.md` |
| Go / stdlib testing | `references/waiting/go.md` |
| Swift / XCTest | `references/waiting/swift.md` |
| Ruby / RSpec | `references/waiting/ruby.md` |
| Java / JUnit 5 / awaitility | `references/waiting/java.md` |

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `sleep(500)` with a "this should be enough" comment | Replace with `wait_for` + condition |
| Polling interval of 1 second because "it's just a test" | 10ms default; the test completes faster and errors surface faster |
| Reusing a cached value inside the poll loop | Re-read fresh state every iteration |
| No timeout (`while !condition { sleep(10) }`) | Add a deadline; hung tests are worse than failed tests |
| Timeout error without context ("timed out waiting") | Name what was being waited for: "timed out waiting for session store to reach size 10" |
| Polling instead of using a signal when a signal exists | Use the signal; polling is fallback |

## Designing the condition

The condition function is the load-bearing part. Two rules:

1. **Idempotent and side-effect-free.** Calling the condition a hundred times must not change the system.
2. **Cheap.** Under 1ms typically. If the check is expensive, widen the interval; don't pay the cost a hundred times.

Example (good):

```
condition = () => sessionStore.size >= 10
```

Example (bad — mutates state):

```
condition = () => {
  sessions = fetchAllSessions();   // network call, expensive, may mutate observability metrics
  return sessions.length >= 10;
}
```

The bad example poll every 10ms will produce 100 network calls per second, pollute metrics, and still may not return when expected.

## Worked examples

### Test-pollution debug — waiting for cleanup to complete

Symptom: test A starts before test B's teardown finishes. Before: `sleep(200)` in test A's setup.

After:

```
wait_for(
  condition = () => globalStore.size() == 0,
  timeout_ms = 5000,
  interval_ms = 10
)
```

Result: test passes immediately when cleanup completes (~50ms), fails loudly with "timed out waiting for globalStore to empty" if cleanup hangs.

### Race-condition repro — waiting for both workers to commit

Symptom: race only reproducible when two workers commit within 2ms of each other. Before: `sleep(50)` between workers.

After:

```
worker1.start()
worker2.start()
wait_for(
  condition = () => worker1.done && worker2.done,
  timeout_ms = 10000
)
assert that both results were merged (tests the race-safe code path)
```

Result: test completes in actual elapsed time, and the race window is captured because both workers are launched before either completes.

## Integration with Phase 1

Condition-based waits are the primary tool for making intermittent bugs deterministic. If Phase 1 cannot produce a 10/10 repro because of timing variability:

1. Find the timing-dependent assertion.
2. Replace the surrounding `sleep(n)` calls with `wait_for` against the actual condition.
3. The bug is now either (a) 10/10 reproducible (and Phase 1 exits) or (b) 0/10 reproducible (which means the original symptom was timing-masked; re-run Phase 1 with the new Phase 1 symptom — what's actually wrong now that timing is controlled).
