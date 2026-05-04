# Example: deploy and invoke a Kernel App

Full walk-through: write an action, deploy it, invoke it from another TypeScript service, stream logs, handle the result.

## The app (`app.ts`)

```ts
import Kernel, { type KernelContext } from '@onkernel/sdk';
import { chromium } from 'playwright';

const kernel = new Kernel();
const app = kernel.app('site-analyzer');

interface AnalyzePayload {
  url: string;
}

interface AnalyzeOutput {
  title: string;
  links: number;
  screenshotPath: string;
}

app.action(
  'analyze',
  async (
    ctx: KernelContext,
    payload: AnalyzePayload,
  ): Promise<AnalyzeOutput> => {
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

      const buf = await page.screenshot();
      const screenshotPath = `/tmp/${ctx.invocation_id}.png`;
      // writeFile takes raw bytes/strings as the positional `contents`;
      // there is no `encoding` parameter — pass the value as-is.
      await kernel.browsers.fs.writeFile(
        session.session_id,
        buf,
        { path: screenshotPath },
      );

      return { title, links, screenshotPath };
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
    "playwright": "^…"
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

`--force` overwrites the same version. CI/CD usually wants a unique version per commit instead.

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
  });

  for await (const evt of await kernel.invocations.follow(inv.id)) {
    switch (evt.event) {
      case 'log':
        console.log(`[${evt.timestamp}] ${evt.message}`);
        break;
      case 'invocation_state': {
        const state = evt.invocation.status;
        if (state === 'succeeded') {
          return JSON.parse(evt.invocation.output ?? 'null') as {
            title: string; links: number; screenshotPath: string;
          };
        }
        if (state === 'failed') {
          throw new Error(evt.invocation.status_reason ?? 'invocation failed');
        }
        break;
      }
      case 'error':
        throw new Error(evt.error.message);
      case 'heartbeat':
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
await kernel.invocations.update(inv.id, { status: 'failed' });
```

If your action's `browsers.create` calls did not set `invocation_id`, those browsers are NOT reaped — they live until their `timeout_seconds`.

## Pull large outputs (>4.5 MB)

`payload` and `output` are JSON-encoded strings, max 4.5 MB each. For results over that limit (multi-MB screenshots, large HTML dumps):

```ts
// Inside the action
await kernel.browsers.fs.writeFile(
  session.session_id,
  JSON.stringify(bigResult),
  { path: '/tmp/result.json' },
);
return { artifactPath: '/tmp/result.json' };

// In the caller
const inv = await kernel.invocations.retrieve(invId);
const tagged = await kernel.invocations.listBrowsers(invId);
const first = tagged.browsers[0];
if (!first) throw new Error(`no browsers tagged to invocation ${invId}`);
const resp = await kernel.browsers.fs.readFile(first.session_id, { path: '/tmp/result.json' });
const bigResult = JSON.parse(await resp.text());
```

Note: the caller must read the file *before* the browser is reaped. Keep the browser alive (extend `timeout_seconds`) or pull artifacts inside the action and PUT them to your own object store.

## Sync invocation pattern (only for sub-100s actions)

```ts
const inv = await kernel.invocations.create({
  app_name: 'site-analyzer',
  action_name: 'analyze',
  version: '1.0.0',
  payload: JSON.stringify({ url }),
});
const out = JSON.parse(inv.output ?? 'null');
```

Sync invocations block on the HTTP request. The hard cap is around 100 seconds — anything that may hit that ceiling must be `async: true`.

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

Then your invocation service reads `version.txt` and passes it as `version: '…'` so deploys and invocations stay in lockstep.
