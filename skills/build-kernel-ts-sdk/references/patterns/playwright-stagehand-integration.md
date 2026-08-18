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

## Stagehand v4 (current — what an unpinned `npm i @browserbasehq/stagehand` gives you)

Latest is **4.0.1**. v4 rewrote the entry point: the `Stagehand` constructor is `private`, `init()` is gone, and `env` / `localBrowserLaunchOptions` / `modelClientOptions` no longer exist. You connect the browser first with the exported `localBrowser` factory, then hand the handle to `Stagehand.create`. Stagehand still connects to Kernel via **local CDP**, **not** the Browserbase API — never pass `apiKey`/`projectId` as Browserbase credentials.

Stagehand 4.0.1 declares `engines: { node: '>=22.18.0' }` — higher than the Node 20 floor above.

**v4 runs as a Chrome extension.** When `localBrowser.connect` is called without an `extensionId`, Stagehand loads the extension into the running browser over CDP by reading it from a path on *that browser's* filesystem. Against a remote Kernel browser you must push the extension there first with `kernel.browsers.fs.uploadZip`.

```ts
import Kernel from '@onkernel/sdk';
import { createReadStream } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Stagehand, localBrowser } from '@browserbasehq/stagehand';
import { z } from 'zod';

const stagehandDist = dirname(fileURLToPath(import.meta.resolve('@browserbasehq/stagehand')));

const kernel = new Kernel();
const session = await kernel.browsers.create({ stealth: true, timeout_seconds: 600 });

try {
  // 1. Mirror the Stagehand extension onto the Kernel browser's filesystem.
  await kernel.browsers.fs.uploadZip(session.session_id, {
    dest_path: join(stagehandDist, 'extension'),
    zip_file: createReadStream(join(stagehandDist, 'assets/stagehand-extension.zip')),
  });

  // 2. Connect. `connect` takes { cdpUrl, extensionId? } and nothing else.
  const browser = await localBrowser.connect({ cdpUrl: session.cdp_ws_url });

  // 3. `model` is optional; Stagehand.create({ browser }) alone type-checks.
  //    modelName is provider-namespaced in v4 — a bare 'gpt-4o' is not a valid value.
  const stagehand = await Stagehand.create({
    browser,
    model: { modelName: 'openai/gpt-4o', apiKey: process.env.OPENAI_API_KEY },
  });

  // act/extract/observe live on the Stagehand instance. There is no `stagehand.page`.
  const [page] = await browser.context.pages();          // existing page — same rule as Playwright
  await page.goto('https://example.com');
  await stagehand.act('click the sign-in button');
  const { data } = await stagehand.extract(
    'extract the page title and the email field',
    z.object({ title: z.string(), emailField: z.string().nullable() }),
  );

  await stagehand.close();
} finally {
  await kernel.browsers.deleteByID(session.session_id);   // the only real cleanup
}
```

`extract` is positional in v4 — `extract(instruction, schema?, options?)` — and resolves to `{ data, ...metadata }`. The old `extract({ instruction, schema })` object form is gone.

## Stagehand v3 (legacy — only if you pin `@browserbasehq/stagehand@^3`)

v3 and v4 entry points are **not** source-compatible. Install with `npm i @browserbasehq/stagehand@^3` or the block below will not compile.

```ts
const stagehand = new Stagehand({
  env: 'LOCAL',
  localBrowserLaunchOptions: {
    cdpUrl: session.cdp_ws_url,
    downloadsPath: './downloads',
    acceptDownloads: true,
  },
  // v3 collapsed modelName + modelClientOptions into one `model` key.
  // Bare model ids here (no provider prefix); shorthand `model: 'gpt-4o'` also works.
  model: { modelName: 'gpt-4o', apiKey: process.env.OPENAI_API_KEY },
});

await stagehand.init();
const page = stagehand.context.pages()[0];   // v3 exposes `context`, never `page`
await page.goto('https://example.com');
await stagehand.act('click the sign-in button');
const data = await stagehand.extract(
  'extract the page title and the email field',
  z.object({ title: z.string(), emailField: z.string().nullable() }),
);
```

In v3 `apiKey` / `projectId` at the top level are the **Browserbase** credentials — leave them unset for Kernel. The model key goes inside `model`.

`stagehand.close()` does the same thing as `browser.close()` — it severs the local connection but does not delete the Kernel browser. Always call `deleteByID`. This is true in both versions.

## Stagehand template

```bash
kernel create --name my-stagehand-app --language typescript --template stagehand --yes
```

All three of `--name`, `--language`, `--template` are required in a non-interactive shell — the CLI fails fast instead of prompting when stdin is not a TTY. `--yes` overwrites an existing directory without confirmation. The `stagehand` template is TypeScript-only.

Which major version it scaffolds is ambiguous: `@onkernel/cli` 0.31.0's own `create --help` describes it as "Implements the Stagehand v3 SDK", while Kernel's integration docs say "The CLI template uses v4." Check the generated `package.json` for the `@browserbasehq/stagehand` range and follow the matching section above.

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
