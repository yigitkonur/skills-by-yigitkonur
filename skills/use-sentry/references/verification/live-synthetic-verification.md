# Live Sentry Verification Harness

How to write and run a dedicated verification script to trigger synthetic test errors, confirm envelope delivery, and verify via Sentry CLI.

## Complete Live Harness Example (`tools/verify-sentry-live.ts`)

```typescript
import { buildServer } from '../src/core/server.js';
import { flushSentry, isSentryInitialized } from '../src/core/obs/sentry.js';

async function verifyLiveSentry() {
  console.log('[1/4] Booting test server...');
  const app = await buildServer();
  await app.listen({ port: 0, host: '127.0.0.1' });
  const address = app.server.address() as { port: number };
  const baseUrl = `http://127.0.0.1:${address.port}`;

  console.log(`[2/4] Server listening on ${baseUrl}. Sentry Initialized: ${isSentryInitialized()}`);

  console.log('[3/4] Sending request to trigger deliberate 500 error...');
  const res = await fetch(`${baseUrl}/api/v1/diagnostics/live-test-error`, {
    headers: {
      'x-api-key': 'test-verification-key',
      'x-request-id': `verify-${Date.now()}`,
    },
  });

  const body = await res.json();
  console.log('Response status:', res.status);

  if (res.status !== 500 || !body.eventId) {
    throw new Error('Expected 500 error with Sentry eventId in response!');
  }

  console.log('[4/4] Flushing Sentry transport...');
  await flushSentry(4000);
  await app.close();

  console.log('Live verification event successfully sent to Sentry! Event ID:', body.eventId);
}

verifyLiveSentry().catch((err) => {
  console.error('Verification failed:', err);
  process.exit(1);
});
```

## Verifying via CLI

```bash
# List recent issues to locate the synthetic error
sentry-cli issues list

# Or using the new CLI:
sentry issue list <org>/<project> -q 'is:unresolved' -t 1h

# Resolve the test issue immediately
sentry-cli issues resolve <ISSUE_ID>
```
