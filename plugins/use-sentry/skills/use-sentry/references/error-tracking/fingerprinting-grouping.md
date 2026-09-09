# Issue Grouping & Custom Fingerprints

How to control how Sentry merges errors into unified issues, preventing alert fatigue from noisy retries or distributed failures.

## Default Grouping vs Alert Fatigue

By default, Sentry groups errors by:
1. Exception type (`TypeError`, `DatabaseError`).
2. Stack trace frames (specifically top in-app frames).

### When Default Grouping Fails:
- **Connection Retries:** A database pool timeout might happen in 5 different helper functions, creating 5 different Sentry issues for the exact same underlying outage.
- **Dynamic Error Messages:** Errors like `Rate limit exceeded for user 123` and `Rate limit exceeded for user 456` might get split into thousands of individual issues if the message string varies.

## Setting Custom Fingerprints in Code

Use `scope.setFingerprint` in `beforeSend` or at the capture callsite:

```typescript
import * as Sentry from '@sentry/node';

export function captureDatabaseError(error: any) {
  Sentry.withScope((scope) => {
    // Group all database connection errors into one canonical issue regardless of caller
    if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
      scope.setFingerprint(['database-connection-outage', error.code]);
    } else if (error.code) {
      // Group by database error code
      scope.setFingerprint(['database-query-error', String(error.code)]);
    } else {
      // Retain default grouping
      scope.setFingerprint(['{{ default }}']);
    }

    Sentry.captureException(error);
  });
}
```

## Fingerprint Rules in Sentry UI / Config

You can also define server-side fingerprinting rules under `Project Settings -> Issue Grouping -> Fingerprint Rules`:

```text
# Group all Stripe rate limit errors together
error.type:StripeRateLimitError -> stripe-rate-limited

# Group all Redis timeouts
error.message:*Redis connection to * failed* -> redis-connection-failure

# Retain default algorithm with secondary tag
error.type:HttpError -> {{ default }}, {{ request.path }}
```

## Special Fingerprint Variables

| Variable | Description |
|---|---|
| `{{ default }}` | The default Sentry grouping fingerprint for the event |
| `{{ transaction }}` | The transaction / route name where the error occurred |
| `{{ error.type }}` | The class name of the exception |
| `{{ error.value }}` | The raw message string of the exception |
