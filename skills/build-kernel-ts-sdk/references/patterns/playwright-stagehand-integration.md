# Playwright and Stagehand integration

Both libraries connect to a Kernel browser via the `cdp_ws_url` returned by `browsers.create`. The integration is the same shape — only the wrapper changes.

## Playwright

```ts
import Kernel from '@onkernel/sdk';
import { chromium } from 'playwright';

const kernel = new Kernel();
const session = await kernel.browsers.create({ stealth: true, timeout_seconds: 300 });

try {
  const browser = await chromium.connectOverCDP(session.cdp_ws_url);
  // CRITICAL: use the existing context and page. Kernel browsers ship with one default
  // context and one open page. Calling browser.newContext() creates a *second* context
  // that does NOT inherit the profile, cookies, or extensions.
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0];

  await page.goto('https://example.com');
  const title = await page.title();
  await page.screenshot({ path: 'shot.png' });
} finally {
  await kernel.browsers.deleteByID(session.session_id);
}
```

Required runtime: **Node 20+**. Bun has known CDP flakiness with Playwright — the SDK emits a warning. Set `KERNEL_SUPPRESS_BUN_WARNING=true` only if you accept the risk.

### Common Playwright pitfalls against a Kernel browser

| Mistake | Result | Fix |
|---|---|---|
| `browser.newContext()` | Cookies, profile, extensions not loaded | Use `browser.contexts()[0]` |
| `context.newPage()` for the first page | Two pages, one orphaned | Use `context.pages()[0]` for the first |
| `await browser.close()` as cleanup | Browser keeps running until `timeout_seconds` | `kernel.browsers.deleteByID(session.session_id)` |
| Skipping `stealth: true` | Bot-detection trips on commercial sites | Default `stealth: true` for non-trivial work |
| Setting `headless: true` and expecting live view | `browser_live_view_url` is undefined | Use headful for live view / replays |
| Awaiting downloads via `page.waitForEvent('download')` only | The CDP event fires before the file is written to Kernel's `fs` | Also poll `kernel.browsers.fs.listFiles` |

## Stagehand v3

Stagehand connects to Kernel via its **local-CDP** entry-point, **not** the Browserbase API. Do not pass `apiKey` or `projectId`.

```ts
import Kernel from '@onkernel/sdk';
import { Stagehand } from '@browserbasehq/stagehand';
import { z } from 'zod';

const kernel = new Kernel();
const session = await kernel.browsers.create({ stealth: true, timeout_seconds: 600 });

const stagehand = new Stagehand({
  env: 'LOCAL',
  localBrowserLaunchOptions: {
    cdpUrl: session.cdp_ws_url,
    downloadsPath: './downloads',
    acceptDownloads: true,
  },
  modelName: 'gpt-4o',
  modelClientOptions: { apiKey: process.env.OPENAI_API_KEY },
});

try {
  await stagehand.init();
  const page = stagehand.page; // Stagehand's enhanced page
  await page.goto('https://example.com');
  await page.act('click the sign-in button');
  const data = await page.extract({
    instruction: 'extract the page title and the email field',
    schema: z.object({ title: z.string(), emailField: z.string().nullable() }),
  });
} finally {
  await stagehand.close();                                  // closes the local Stagehand wrapper
  await kernel.browsers.deleteByID(session.session_id);     // DELETES the Kernel browser
}
```

`stagehand.close()` does the same thing as `browser.close()` — it severs the local connection but does not delete the Kernel browser. Always call `deleteByID`.

## Stagehand template

```bash
kernel create --template stagehand
```

Scaffolds a ready-to-deploy Kernel App with Stagehand wired up — useful as a starting point.

## Puppeteer

Same pattern as Playwright with `puppeteer.connect`:

```ts
import puppeteer from 'puppeteer';

const browser = await puppeteer.connect({ browserWSEndpoint: session.cdp_ws_url });
const page = (await browser.pages())[0];                    // existing page
await page.goto('https://example.com');
```

Same warnings: don't `browser.disconnect()` and assume cleanup; don't `browser.newPage()` instead of using the existing one.

## Browser Use (Python only — TS users see workarounds)

`browser-use` is Python. There is no native TypeScript binding. If your TS service needs Browser Use's agent loop, deploy a Python Kernel App and `invocations.create` it from your TS service. See `references/patterns/integrations-matrix.md` for the integration shape.
