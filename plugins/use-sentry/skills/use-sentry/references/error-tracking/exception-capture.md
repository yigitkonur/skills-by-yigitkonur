# Core Error Tracking: Exception Capture

How to reliably capture unhandled runtime errors, edge crashes, and script exceptions across Node.js, browser, and serverless runtimes.

## 1. Unhandled Rejections & Uncaught Exceptions

By default, `@sentry/node` automatically enables `onUnhandledRejectionIntegration` and `onUncaughtExceptionIntegration` inside `Sentry.init()`. **Do NOT manually attach redundant `process.on('unhandledRejection')` handlers that call `Sentry.captureException`**, as this will result in duplicate error reports.

### Customizing Uncaught Exception Handling

If you want custom process exit behavior or crash logging:

```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  integrations: [
    // Configure default uncaught exception integration behavior
    Sentry.onUncaughtExceptionIntegration({
      exitEvenIfRestarts: true,
      onFatalError: async (error) => {
        console.error('Fatal crash intercepted by Sentry:', error.message);
        // Flush buffered events to Sentry before exit
        await Sentry.flush(2000);
        process.exit(1);
      },
    }),
  ],
});
```

### Graceful Shutdown Flush Hook

For SIGTERM / SIGINT termination in Kubernetes, Docker, or serverless containers:

```typescript
async function handleGracefulShutdown(signal: string) {
  console.log(`Received ${signal}. Flushing Sentry and exiting...`);
  try {
    await Sentry.close(2000); // Closes transport and drains pending events
  } finally {
    process.exit(0);
  }
}

process.on('SIGTERM', () => handleGracefulShutdown('SIGTERM'));
process.on('SIGINT', () => handleGracefulShutdown('SIGINT'));
```

## 2. Capturing Handled Exceptions with Rich Context

When handling an exception in a `try / catch` block, do NOT discard the stack trace or surrounding context:

```typescript
try {
  await executeCriticalOperation(payload);
} catch (error: any) {
  // Capture with custom tags and extra debugging metadata
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

  // Re-throw or handle gracefully according to business logic
  throw error;
}
```

## 3. Capturing Non-Exception Messages

For business logic anomalies, security alerts, or invariant violations:

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
import * as Sentry from '@sentry/edge';

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    try {
      return await handleRequest(request);
    } catch (err: any) {
      Sentry.captureException(err);
      // Wait for network flush before edge worker terminates
      ctx.waitUntil(Sentry.flush(2000));
      return new Response('Internal Server Error', { status: 500 });
    }
  }
};
```
