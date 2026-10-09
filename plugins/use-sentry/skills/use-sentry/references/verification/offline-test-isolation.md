# Zero-Network Offline Test Gate Discipline

How to guarantee unit and integration test suites run 100% offline without hitting Sentry or leaking network requests.

## The Invariant

An offline test gate (e.g. `npm test`) must:
1. **Spend zero dollars and make zero network requests.**
2. **Never fail because an internet connection dropped or an API token expired.**
3. **Never attempt to send mock test exceptions to production Sentry.**

## Pattern 1: Native SDK v8 No-Op When DSN is Unset

Sentry SDK v8 natively operates in clean no-op mode when `dsn` is omitted, empty, or undefined:

```typescript
import * as Sentry from '@sentry/node';

// src/core/obs/sentry.ts
export function setupSentry(options?: { dsn?: string }) {
  const dsn = options?.dsn ?? process.env.SENTRY_DSN;
  if (!dsn || !dsn.trim()) {
    // Zero-network offline mode: SDK natively no-ops if initialized with empty DSN,
    // or you can cleanly return without initializing.
    return;
  }

  Sentry.init({
    dsn,
    tracesSampleRate: 1.0,
  });
}
```

When uninitialized or initialized without a DSN, `Sentry.captureException()` safely executes without making network requests.

## Pattern 2: Unit Test Suite Verification

Create a dedicated assertion test verifying that when `SENTRY_DSN` is absent:
1. Calling `Sentry.init` or setup function does not crash.
2. `Sentry.captureException()` executes cleanly without throwing or making network calls.
3. No uncaught rejections or network calls occur.

```typescript
import { describe, it, expect } from 'vitest';
import * as Sentry from '@sentry/node';
import { setupSentry } from '../../src/core/obs/sentry.js';

describe('Sentry Offline Isolation Gate', () => {
  it('does not transmit when SENTRY_DSN is unset', () => {
    delete process.env.SENTRY_DSN;
    setupSentry();
    
    // Sentry.getClient() is undefined or has no active transport
    const client = Sentry.getClient();
    expect(client?.getOptions().dsn).toBeFalsy();
  });

  it('safely handles Sentry.captureException when offline', () => {
    expect(() => {
      Sentry.captureException(new Error('Offline unit test error'));
    }).not.toThrow();
  });
});
```
