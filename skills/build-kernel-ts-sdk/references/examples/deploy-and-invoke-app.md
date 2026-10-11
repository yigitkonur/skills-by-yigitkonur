# Example: deploy and invoke a Kernel App

Full walk-through: write an action, deploy it, invoke it from another TypeScript service, stream logs, handle the result.

Source note: checked against `@onkernel/sdk@0.123.0`, `@onkernel/cli@0.47.0` and the docs pages `apps/*`. Payload-size docs conflict (64 KB vs 4.5 MB); use file/object-storage paths for large artifacts.

## The app (`app.ts`)

```ts
import Kernel, { type KernelContext } from '@onkernel/sdk';
import { chromium } from 'playwright-core';

const kernel = new Kernel();
const app = kernel.app('site-analyzer');

interface AnalyzePayload {
  url: string;
}

interface AnalyzeOutput {
  title: string;
  links: number;
}

app.action(
  'analyze',
  async (
    ctx: KernelContext,
    payload?: AnalyzePayload,
  ): Promise<AnalyzeOutput> => {
    if (!payload?.url) throw new Error('payload.url is required');
    const session = await kernel.browsers.create({
      stealth: true,
      timeout_seconds: 600,
      invocation_id: ctx.invocation_id, // tag for cleanup-on-stop
    });

    try {
      const browser = await chromium.connectOverCDP(session.cdp_ws_url);
      const page = browser.contexts()[0].pages()[0];
      await page.goto(payload.url, { waitUntil: 'networkidle' });

      const title = await page.title();
      const links = await page.$$eval('a', els => els.length);

      // Files written to the browser's fs disappear with the browser (deleted in `finally`).
      // Return small JSON here; see "Pull large outputs" below for artifacts.
      return { title, links };
    } finally {
      await kernel.browsers.deleteByID(session.session_id);
    }
  },
);
```

`package.json`:

```json
{
  "name": "site-analyzer",
  "type": "module",
  "dependencies": {
    "@onkernel/sdk": "^…",
    "playwright-core": "^…"
  }
}
```

## Deploy

```bash
kernel deploy app.ts \
  --version 1.0.0 \
  --env-file .env \
  --force
```

`app.ts` sits next to `package.json` and a lockfile (`package-lock.json`, `pnpm-lock.yaml` or `bun.lock`): the CLI uploads the entrypoint's directory. `--force` overwrites the same version; CI/CD usually wants a unique version per commit instead. Omitting `--version` deploys the label `latest`.

## Invoke from another TS service

```ts
// invoke.ts (your service)
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();

async function analyzeSite(url: string) {
  const inv = await kernel.invocations.create({
    app_name: 'site-analyzer',
    action_name: 'analyze',
    version: '1.0.0',
    async: true,                              // long enough that sync would time out
    async_timeout_seconds: 1800,
    payload: JSON.stringify({ url }),
  }, { maxRetries: 0 });                      // a retried create would start a second billed run

  for await (const evt of await kernel.invocations.follow(inv.id)) {
    switch (evt.event) {
      case 'log':
        console.log(`[${evt.timestamp}] ${evt.message}`);
        break;
      case 'invocation_state': {
        const state = evt.invocation.status;
        if (state === 'succeeded') {
          return JSON.parse(evt.invocation.output ?? 'null') as {
            title: string; links: number;
          };
        }
        if (state === 'failed') {
          throw new Error(evt.invocation.status_reason ?? 'invocation failed');
        }
        break;
      }
      case 'error':
        throw new Error(evt.error.message);
      case 'sse_heartbeat':
        // keepalive
        break;
    }
  }
  throw new Error('stream ended without terminal state');
}

const result = await analyzeSite('https://example.com');
console.log(result);
```

## Stop early

```ts
// Stop the invocation and reap any browsers tagged with its invocation_id
await kernel.invocations.update(invId, { status: 'failed' });
```

If your action's `browsers.create` calls did not set `invocation_id`, those browsers are NOT reaped — they live until their `timeout_seconds`.

## Pull large outputs / avoid payload-size ambiguity

Kernel docs currently disagree on payload size: `apps/develop` and CLI docs say 64 KB, while `apps/invoke` says stringified JSON payloads max at 4.5 MB. Treat payload/output as control-plane JSON, not an artifact channel. For multi-MB screenshots, large HTML dumps, or archives, use one of these patterns.

**Pattern A (unverified, depends on the browser outliving the action): caller reads the browser fs, then reaps.** Docs only guarantee that `invocations.update(..., { status: 'failed' })` and `deleteBrowsers` destroy browsers tagged with the invocation, and that `listBrowsers` returns *active* sessions. Nothing documents that a tagged browser survives after the action returns, so give it a long `timeout_seconds` and treat a missing browser as a normal outcome:

```ts
import Kernel, { type KernelContext } from '@onkernel/sdk';

const kernel = new Kernel();

// Inside the action — NO deleteByID in finally. Tag with invocation_id so the caller can find/reap it.
async function produce(ctx: KernelContext, bigResult: unknown) {
  const session = await kernel.browsers.create({
    stealth: true,
    timeout_seconds: 600,
    invocation_id: ctx.invocation_id,
  });
  await kernel.browsers.fs.writeFile(
    session.session_id,
    JSON.stringify(bigResult),
    { path: '/tmp/result.json' },
  );
  return { artifactPath: '/tmp/result.json' };
}

// In the caller
async function collect(invId: string) {
  const tagged = await kernel.invocations.listBrowsers(invId);
  const first = tagged.browsers[0];
  if (!first) throw new Error(`no browsers tagged to invocation ${invId}`);
  const resp = await kernel.browsers.fs.readFile(first.session_id, { path: '/tmp/result.json' });
  const bigResult = JSON.parse(await resp.text());
  await kernel.invocations.deleteBrowsers(invId); // reap when done
  return bigResult;
}
```

**Pattern B — Action uploads to your own object store, deletes the browser as usual:**

Inside the action, `PUT` the artifact to S3/GCS/R2 and return only the URL. The action's `finally { deleteByID }` stays. This is the safer default for production: no browser has to stay alive for the caller to fetch from.

## Sync invocation pattern (only for sub-100s actions)

```ts
const inv = await kernel.invocations.create(
  {
    app_name: 'site-analyzer',
    action_name: 'analyze',
    version: '1.0.0',
    payload: JSON.stringify({ url }),
  },
  { timeout: 110_000, maxRetries: 0 }, // default client timeout is 60 s with 2 retries
);
const out = JSON.parse(inv.output ?? 'null');
```

Sync invocations block on the HTTP request and time out after 100 seconds; anything that may approach that must be `async: true`. The choice is per request, no redeploy.

CLI note: `kernel invoke <app> <action>` submits an async invocation and then follows the SSE stream, printing logs and the result until the run ends (Ctrl+C cancels it). `--sync` (`-s`) is a single POST with a 60 s timeout and no log stream.

## CI deploy snippet

```bash
VERSION="$(git rev-parse --short HEAD)"
kernel deploy app.ts \
  --version "$VERSION" \
  --env-file .env.production \
  --force

cat <<EOF > version.txt
$VERSION
EOF
```

Then your invocation service reads `version.txt` and passes it as `version: '…'` so deploys and invocations stay in lockstep. (`version: 'latest'` is also accepted; it is just the label `kernel deploy` uses when `--version` is omitted, so pin an explicit version in CI.)
