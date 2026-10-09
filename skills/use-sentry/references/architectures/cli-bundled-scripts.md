# Architecture: Standalone CLIs & Bundled `.mjs` Scripts

How to instrument CLI tools, esbuild/rollup bundles, and standalone `.mjs` scripts so telemetry flushes before process termination.

## The CLI Premature Exit Trap

In a web server, the event loop remains open indefinitely.
In a CLI or short-lived script:
```bash
node script.mjs --target invalid
```
When an exception occurs, the script terminates immediately (`process.exit(1)`).
Because Sentry's envelope transmission is asynchronous, Node's event loop shuts down before the HTTP POST request to Sentry completes, causing the error report to be dropped silently.

## The Solution: Explicit Sentry Flush

Before exiting, always await `Sentry.flush(timeoutMs)` or `Sentry.close(timeoutMs)`:

```typescript
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 1.0,
});

export async function flushTelemetry(timeoutMs: number = 3000): Promise<boolean> {
  try {
    return await Sentry.flush(timeoutMs);
  } catch {
    return false;
  }
}
```

## CLI Wrapper Architecture Pattern (`cli.ts`)

```typescript
import * as Sentry from '@sentry/node';

export async function runCli(argv: string[]): Promise<number> {
  // 1. Initialize Sentry at entrypoint (natively no-ops if SENTRY_DSN is absent)
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    tracesSampleRate: 1.0,
  });

  try {
    // 2. Parse arguments and execute pipeline
    await executePipeline(argv);
    
    // 3. Normal clean exit: flush telemetry before returning
    await Sentry.flush(2000);
    return 0;
  } catch (error: any) {
    // 4. Capture failure to Sentry using canonical SDK v8
    Sentry.captureException(error, {
      extra: { argv },
    });

    // 5. Guaranteed flush before process termination
    await Sentry.flush(3000);
    
    console.error(`Fatal CLI Error: ${error.message}`);
    return 1;
  }
}

if (process.argv[1] && process.argv[1].endsWith('cli.js')) {
  runCli(process.argv.slice(2)).then((code) => {
    process.exit(code);
  });
}
```
