# Example: minimal browser-screenshot

The smallest end-to-end Kernel-TS flow — create a stealth browser, navigate, screenshot, terminate. Use as a sanity check after install or as a starting scaffold.

## Setup

```bash
npm install @onkernel/sdk playwright
export KERNEL_API_KEY=…
```

## Code (`screenshot.ts`)

```ts
import Kernel from '@onkernel/sdk';
import { chromium } from 'playwright';
import fs from 'node:fs';

async function main() {
  const kernel = new Kernel();

  const session = await kernel.browsers.create({
    stealth: true,
    timeout_seconds: 300,
    viewport: { width: 1280, height: 800 },
  });

  try {
    const browser = await chromium.connectOverCDP(session.cdp_ws_url);
    const ctx = browser.contexts()[0];
    const page = ctx.pages()[0];

    await page.goto('https://example.com', { waitUntil: 'networkidle' });

    const png = await page.screenshot();
    fs.writeFileSync('./shot.png', png);

    console.log('title:', await page.title());
    console.log('live view:', session.browser_live_view_url ?? '(headless)');
  } finally {
    await kernel.browsers.deleteByID(session.session_id);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
```

## Run

```bash
npx tsx screenshot.ts
```

## Verify

- `shot.png` exists and contains the rendered page
- The terminal printed the page title
- (Headful) the live view URL was reachable while the script ran
- The browser is gone — `kernel.browsers.list()` does not show the `session_id`

## Variations

**In-VM execution (no CDP roundtrip):**

```ts
const { result } = await kernel.browsers.playwright.execute(session.session_id, {
  code: `
    await page.goto('https://example.com', { waitUntil: 'networkidle' });
    const buf = await page.screenshot();
    return { title: await page.title(), bytes: buf.length };
  `,
  timeout_sec: 60,
});
```

`result` is the JSON-serialised return value. To get the screenshot bytes back, write to the browser VM's `fs` and read out via `kernel.browsers.fs.readFile`:

```ts
await kernel.browsers.playwright.execute(session.session_id, {
  code: `
    await page.goto('https://example.com');
    const buf = await page.screenshot();
    await require('fs/promises').writeFile('/tmp/shot.png', buf);
  `,
});
const resp = await kernel.browsers.fs.readFile(session.session_id, { path: '/tmp/shot.png' });
fs.writeFileSync('./shot.png', Buffer.from(await resp.arrayBuffer()));
```

**Computer-controls (no Playwright):**

```ts
const resp = await kernel.browsers.computer.captureScreenshot(session.session_id);
fs.writeFileSync('./shot.png', Buffer.from(await resp.arrayBuffer()));
```

For navigation via computer-controls, type the URL into the address bar:

```ts
await kernel.browsers.computer.batch(session.session_id, {
  actions: [
    { type: 'press_key', press_key: { keys: ['Meta', 'l'] } }, // or ['Control', 'l']
    { type: 'type_text', type_text: { text: 'https://example.com' } },
    { type: 'press_key', press_key: { keys: ['Enter'] } },
  ],
});
```
