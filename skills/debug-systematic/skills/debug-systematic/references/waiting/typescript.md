# TypeScript / Jest / Vitest — Condition-Based Waiting

Ported from obra's reference `condition-based-waiting-example.ts`. Drop-in utilities that replace `sleep(n)` in Jest or Vitest tests.

## Utilities

```typescript
// poll-utils.ts
export interface WaitOptions {
  timeoutMs?: number;
  intervalMs?: number;
  description?: string;
}

export async function waitFor<T>(
  condition: () => T | Promise<T> | null | undefined,
  { timeoutMs = 5_000, intervalMs = 10, description = 'condition' }: WaitOptions = {}
): Promise<T> {
  const deadline = Date.now() + timeoutMs;
  let lastError: unknown = undefined;
  while (Date.now() < deadline) {
    try {
      const result = await condition();
      if (result) return result as T;
    } catch (err) {
      lastError = err;
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error(
    `waitFor timed out after ${timeoutMs}ms: ${description}${
      lastError ? ` (last error: ${String(lastError)})` : ''
    }`,
  );
}

export async function waitForEventCount(
  getCount: () => number | Promise<number>,
  expected: number,
  opts: WaitOptions = {},
): Promise<void> {
  await waitFor(
    async () => (await getCount()) >= expected,
    { ...opts, description: opts.description ?? `event count >= ${expected}` },
  );
}

export async function waitForEventMatch<T>(
  getEvents: () => T[] | Promise<T[]>,
  predicate: (e: T) => boolean,
  opts: WaitOptions = {},
): Promise<T> {
  return waitFor(
    async () => {
      const events = await getEvents();
      return events.find(predicate);
    },
    { ...opts, description: opts.description ?? 'matching event' },
  );
}
```

## Usage

```typescript
import { waitFor, waitForEventCount } from './poll-utils';

test('cleanup completes before next test', async () => {
  await waitFor(() => globalStore.size === 0, {
    timeoutMs: 5_000,
    description: 'globalStore to empty',
  });
  expect(globalStore.size).toBe(0);
});

test('both workers commit', async () => {
  await waitForEventCount(() => commitLog.length, 2, {
    description: 'two worker commits',
  });
  expect(new Set(commitLog.map((c) => c.workerId)).size).toBe(2);
});
```

## Test-framework integration

**Jest** — default timeout is 5s per test; set per-test if your condition takes longer:

```typescript
test('slow event', async () => { /* ... */ }, 30_000);
```

**Vitest** — identical API; pass timeout as third arg to `test`.

**Fake timers** — if the test uses `jest.useFakeTimers()` / `vi.useFakeTimers()`, `setTimeout` inside `waitFor` will not advance. Either advance timers manually (`jest.advanceTimersByTime(10)`) in the loop or avoid fake timers for tests that use `waitFor`.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| `await new Promise(r => setTimeout(r, 500))` with a "should be enough" comment | Replace with `waitFor` + named condition |
| Condition function makes a network call every iteration | Cache what's safe to cache; keep the condition cheap |
| Swallowing all errors inside the condition | Record as `lastError` so the timeout message includes it (see utility above) |
| Timeout without a `description` | The default "condition" tells nothing; always name what you're waiting for |
