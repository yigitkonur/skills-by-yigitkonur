# Zero-Network Offline Test Gate Discipline

How to guarantee unit and integration test suites run 100% offline without hitting Sentry or leaking network requests.

## The Invariant

An offline test gate (e.g. `npm test`) must:
1. **Spend zero dollars and make zero network requests.**
2. **Never fail because an internet connection dropped or an API token expired.**
3. **Never attempt to send mock test exceptions to production Sentry.**

## Pattern 1: No-Op When DSN is Unset

Design the Sentry initialization module so that an empty, missing, or whitespace-only DSN cleanly results in a no-op:

```typescript
// src/core/obs/sentry.ts
let initialized = false;

export function initSentry(options?: { dsn?: string }) {
  if (initialized) return;

  const dsn = options?.dsn || process.env.SENTRY_DSN;
  if (!dsn || !dsn.trim()) {
    // Zero-network offline mode: Do not call Sentry.init()
    return;
  }

  Sentry.init({ dsn, ... });
  initialized = true;
}

export function captureAppException(error: unknown): string | undefined {
  if (!initialized) {
    return undefined;
  }
  return Sentry.captureException(error);
}
```

## Pattern 2: Unit Test Suite Verification

Create a dedicated assertion test verifying that when `SENTRY_DSN` is absent:
1. `initSentry()` does not crash.
2. `captureAppException()` returns `undefined` safely.
3. No uncaught rejections or network calls occur.

```typescript
import { describe, it, expect } from 'vitest';
import { initSentry, isSentryInitialized, captureAppException } from '../../src/core/obs/sentry.js';

describe('Sentry Offline Isolation Gate', () => {
  it('does not initialize when SENTRY_DSN is unset', () => {
    delete process.env.SENTRY_DSN;
    initSentry();
    expect(isSentryInitialized()).toBe(false);
  });

  it('safely handles captureAppException when offline', () => {
    const result = captureAppException(new Error('Offline unit test error'));
    expect(result).toBeUndefined();
  });
});
```
