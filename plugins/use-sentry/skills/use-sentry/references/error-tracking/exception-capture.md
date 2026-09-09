# Core Error Tracking: Exception Capture

How to reliably capture unhandled runtime errors, edge crashes, and script exceptions across Node.js, browser, and serverless runtimes.

## 1. Unhandled Rejections & Uncaught Exceptions

In Node.js, unhandled promise rejections or uncaught exceptions can silently terminate worker threads or cause memory leaks.

```typescript
import * as Sentry from '@sentry/node';

export function registerProcessErrorHandlers() {
  process.on('unhandledRejection', (reason: unknown, promise: Promise<any>) => {
    Sentry.withScope((scope) => {
      scope.setExtra('unhandledPromise', String(promise));
      scope.setLevel('fatal');
      Sentry.captureException(reason);
    });
  });

  process.on('uncaughtException', async (error: Error) => {
    Sentry.withScope((scope) => {
      scope.setLevel('fatal');
      Sentry.captureException(error);
    });

    // Give Sentry transport 2 seconds to flush before terminating
    await Sentry.flush(2000);
    process.exit(1);
  });
}
```

## 2. Capturing Handled Exceptions with Rich Context

When handling an exception in a `try / catch` block, do NOT lose the stack trace or surrounding context:

```typescript
try {
  await executeCriticalOperation(payload);
} catch (error: any) {
  // Capture with custom tags and extras for this specific failure
  Sentry.captureException(error, {
    tags: {
      operation: 'executeCriticalOperation',
      payloadId: payload.id,
      retryCount: payload.retries,
    },
    extra: {
      systemState: getSystemStateSummary(),
    },
  });

  // Re-throw or handle gracefully
  throw error;
}
```

## 3. Capturing Non-Exception Messages

For business logic anomalies, security breaches, or unexpected state transitions:

```typescript
if (suspiciousLoginAttempts > 10) {
  Sentry.captureMessage(`High volume login attempts detected for account ${accountId}`, {
    level: 'warning',
    tags: { security_alert: 'brute_force' },
  });
}
```

## 4. Edge Runtime / Worker Exception Traps

In Cloudflare Workers, Vercel Edge, or AWS Lambda:
```typescript
import * as Sentry from '@sentry/edge'; // or @sentry/aws-serverless

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    try {
      return await handleRequest(request);
    } catch (err: any) {
      Sentry.captureException(err);
      // Ensure async logs finish before worker dies
      ctx.waitUntil(Sentry.flush(2000));
      return new Response('Internal Error', { status: 500 });
    }
  }
};
```
