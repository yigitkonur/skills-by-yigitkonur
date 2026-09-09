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

## The Solution: Explicit `flushSentry`

Before exiting, always await `Sentry.flush(timeoutMs)`:

```typescript
import * as Sentry from '@sentry/node';

export async function flushSentry(timeoutMs: number = 3000): Promise<boolean> {
  try {
    return await Sentry.flush(timeoutMs);
  } catch {
    return false;
  }
}
```

## CLI Wrapper Architecture Pattern (`cli.ts`)

```typescript
import { initSentry, flushSentry, captureAppException } from './sentry.js';

export async function runCli(argv: string[]): Promise<number> {
  // 1. Initialize Sentry at entrypoint
  initSentry();

  try {
    // 2. Parse arguments and execute pipeline
    await executePipeline(argv);
    
    // 3. Normal clean exit: flush telemetry before returning
    await flushSentry(2000);
    return 0;
  } catch (error: any) {
    // 4. Capture failure to Sentry
    captureAppException(error, { argv });

    // 5. Guaranteed flush before process termination
    await flushSentry(3000);
    
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
