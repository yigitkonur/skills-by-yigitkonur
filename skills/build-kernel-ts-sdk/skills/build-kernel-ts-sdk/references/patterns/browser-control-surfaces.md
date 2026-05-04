# Browser control surfaces

Kernel exposes a Chromium browser in a unikernel VM. Four surfaces drive it. Pick one per task — mixing surfaces in the same flow is allowed but rarely needed.

## Decision tree

```
What are you doing?
├── Long-lived interactive session, full Playwright/Puppeteer API
│   └─► Raw CDP via `chromium.connectOverCDP(session.cdp_ws_url)`
├── Hot-path scripted operation (scrape, fill, screenshot) called many times
│   └─► `kernel.browsers.playwright.execute(id, { code })` — runs in the browser VM, no CDP roundtrip
├── Vision-loop / VLM-driven agent (computer use)
│   └─► `kernel.browsers.computer.*` — screenshot + mouse/keyboard primitives
├── HTTP from the browser's TLS fingerprint (no DOM needed)
│   └─► `kernel.browsers.curl(id, { url })`
└── WebDriver BiDi client (Vibium etc.)
    └─► Pass `session.webdriver_ws_url` instead of CDP
```

## Surface 1 — Raw CDP

```ts
import { chromium } from 'playwright';

const browser = await chromium.connectOverCDP(session.cdp_ws_url);
const ctx = browser.contexts()[0];                  // never browser.newContext()
const page = ctx.pages()[0];                        // never ctx.newPage()
await page.goto('https://example.com');
const title = await page.title();
```

When to use:

- Sessions that need to span many user interactions
- Stagehand / Browser Use / Claude Agent SDK integrations (they expect CDP)
- Live debugging via Chrome DevTools attached to the same CDP

Cost: every call is a network round-trip from your service to the browser VM. For tight inner loops over many pages, switch to surface 2.

## Surface 2 — Playwright execute (in-VM)

```ts
const { result } = await kernel.browsers.playwright.execute(session.session_id, {
  code: `
    await page.goto('https://example.com');
    const title = await page.title();
    const links = await page.$$eval('a', els => els.map(el => el.href));
    return { title, links };
  `,
  timeout_sec: 60,                            // default 60 seconds
});
```

When to use:

- Bulk extraction or scripted multi-step operations
- Anywhere CDP latency adds up — the script runs in the browser VM with `page`, `context`, and `browser` already in scope
- Returning structured results without serialising every value over CDP

Caveats:

- The code body is a string; pass closures' values via JSON-encoded environment variables or via the response shape, not via JavaScript closures from your service.
- The VM has no access to `process.env` from your service. If the script needs an API key, pass it in the code body literal or fetch it from inside the VM.
- Stack traces are returned as strings; budget for plaintext debugging.

## Surface 3 — Computer controls

```ts
// Screenshot returns a raw Response — wire to a VLM directly
const resp = await kernel.browsers.computer.captureScreenshot(session.session_id);
const png = Buffer.from(await resp.arrayBuffer());

// Mouse
await kernel.browsers.computer.clickMouse(session.session_id, { x: 100, y: 200, button: 'left' });
await kernel.browsers.computer.moveMouse(session.session_id, { x: 400, y: 300 });
// dragMouse takes an ordered path of [x, y] pairs (>= 2 points)
await kernel.browsers.computer.dragMouse(session.session_id, {
  path: [[100, 100], [300, 300]],
});

// Keyboard
await kernel.browsers.computer.typeText(session.session_id, {
  text: 'hello world',
  delay: 30,                  // optional ms between keystrokes
});
// pressKey takes an ARRAY of keys (chord supported via hold_keys)
await kernel.browsers.computer.pressKey(session.session_id, { keys: ['Enter'] });

// Scroll requires anchor coordinates plus delta_x/delta_y
await kernel.browsers.computer.scroll(session.session_id, {
  x: 400, y: 300,
  delta_y: 500,
});

// Clipboard
await kernel.browsers.computer.writeClipboard(session.session_id, { text: 'pasted' });
await kernel.browsers.computer.readClipboard(session.session_id);

// Cursor visibility uses `hidden`, not `visible`
await kernel.browsers.computer.setCursorVisibility(session.session_id, { hidden: true });

// Batch — actions are a discriminated union: { type, <type>: { ... } }
await kernel.browsers.computer.batch(session.session_id, {
  actions: [
    { type: 'move_mouse', move_mouse: { x: 100, y: 200 } },
    { type: 'click_mouse', click_mouse: { x: 100, y: 200, button: 'left' } },
    { type: 'type_text',  type_text:  { text: 'search query' } },
    { type: 'press_key',  press_key:  { keys: ['Enter'] } },
  ],
});
```

When to use:

- Vision-loop agents (Claude computer-use, OpenAI computer-use, custom VLM)
- Sites that defeat DOM-based automation but accept human-like input
- Demos / human-handoff flows where the user watches via live view

Avoid mixing computer-controls with CDP `page.click` on the same flow — both are valid but they read differently in replays and logs.

## Surface 4 — Browser-side HTTP

```ts
// Curl through the browser's TLS fingerprint and current cookies
const res = await kernel.browsers.curl(session.session_id, {
  url: 'https://api.example.com/data',
  method: 'GET',
  headers: { 'Accept': 'application/json' },
  response_encoding: 'utf8',     // or 'base64'
  timeout_ms: 30_000,
});

// POST a JSON body — same shape, just set method + body
const res2 = await kernel.browsers.curl(session.session_id, {
  url: 'https://api.example.com/submit',
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ q: 'test' }),
  response_encoding: 'utf8',
});
```

When to use:

- API calls from inside the browser's network stack (cookies, proxy, fingerprint all preserved)
- Bypassing CDP for non-DOM work
- Hitting endpoints that block standard `fetch` from your server

## WebDriver BiDi

For Vibium, Selenium-style clients, or any other WebDriver BiDi consumer, use `session.webdriver_ws_url` in place of `cdp_ws_url`. Same lifecycle rules apply — `deleteByID` for cleanup.

## Mixing surfaces

You can use multiple surfaces in the same session — they all share the same browser VM and cookies. Common combinations:

- **Live view + computer-controls** — embed the live view URL in your UI, use `computer.*` to drive the browser based on screenshots.
- **CDP setup, `playwright.execute` for bulk** — connect once, use Playwright for navigation, switch to in-VM execute for tight extraction loops.
- **CDP + `browsers.curl`** — drive the page with Playwright, hit JSON endpoints from inside the browser's TLS fingerprint without spawning a new context.
