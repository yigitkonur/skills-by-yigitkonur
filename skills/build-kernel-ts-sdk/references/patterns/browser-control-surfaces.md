# Browser control surfaces

Kernel exposes a Chromium browser in a unikernel VM. Eight surfaces drive it. Pick the right surface for your workload — mixing surfaces in the same session is supported because they all share the same browser VM and session state.

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
│   └─► `kernel.browsers.curl(id, { url })` or `kernel.browsers.fetch(id, url)`
├── WebDriver BiDi client (Vibium etc.)
│   └─► Pass `session.webdriver_ws_url` instead of CDP
├── Persistent interactive Node.js scripting in VM across calls
│   └─► Browser REPL via `kernel.browsers.repl.*` or `kernel browsers repl`
├── Page-declared or custom Model Context Protocol tools
│   └─► WebMCP via `kernel.browsers.webmcp.*` or `kernel browsers webmcp`
└── Direct OS-level commands, PTY, or local tooling inside VM
    └─► Process execution via `kernel.browsers.process.*` or `kernel browsers process`
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
const res = await kernel.browsers.playwright.execute(session.session_id, {
  code: `
    await page.goto('https://example.com');
    const title = await page.title();
    const links = await page.$$eval('a', els => els.map(el => el.href));
    return { title, links };
  `,
  timeout_sec: 60,                            // default 60, max 300
});

// Response is { success, error?, result, stderr, stdout } — always check `success`
// before using `result`. `stderr` / `stdout` are captured from the script's logs.
if (!res.success) throw new Error(`playwright.execute failed: ${res.error}`);
// `res.result` is typed `unknown` and may be undefined — assert the runtime shape.
const { title, links } = res.result as { title: string; links: string[] };
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
// pressKey takes a `keys` array; each item is ONE press, emitted in sequence.
// A chord must therefore be a SINGLE combined item in xdotool keysym syntax,
// e.g. 'Ctrl+l' or 'Ctrl+Shift+Tab' — `keys: ['Ctrl', 'l']` taps Ctrl, then l.
// Use `hold_keys` for a separate set of modifiers held across the whole `keys`
// sequence (e.g. hold Shift while pressing arrows). `duration` holds each press.
await kernel.browsers.computer.pressKey(session.session_id, { keys: ['Ctrl+l'] });
// A real sequence — two independent presses, in order:
await kernel.browsers.computer.pressKey(session.session_id, { keys: ['Ctrl+a', 'Delete'] });

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

// Batch — actions are a discriminated union { type, <type>: { ... } }
// with eight valid types: 'click_mouse' | 'move_mouse' | 'type_text' |
// 'press_key' | 'scroll' | 'drag_mouse' | 'set_cursor' | 'sleep'.
await kernel.browsers.computer.batch(session.session_id, {
  actions: [
    { type: 'move_mouse',   move_mouse:   { x: 100, y: 200 } },
    { type: 'click_mouse',  click_mouse:  { x: 100, y: 200, button: 'left' } },
    { type: 'type_text',    type_text:    { text: 'search query' } },
    { type: 'press_key',    press_key:    { keys: ['Enter'] } },
    { type: 'sleep',        sleep:        { duration_ms: 250 } },     // pause between actions
    { type: 'set_cursor',   set_cursor:   { hidden: true } },         // hide cursor for clean screenshots
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

## Surface 5 — Persistent Browser REPL

A long-lived Node.js runtime inside the browser VM where top-level variables, bindings, closures, and imports persist across calls until explicitly reset.

```ts
// Initial call sets up state, imports libraries, or navigates
const initRes = await kernel.browsers.repl(session.session_id, {
  code: `
    const { chromium } = require('playwright');
    globalThis.browser = await chromium.connectOverCDP('http://localhost:9222');
    globalThis.page = (await globalThis.browser.contexts())[0].pages()[0];
    await globalThis.page.goto('https://example.com');
    repl.write('Page loaded: ' + (await globalThis.page.title()));
  `,
});
console.log('REPL outputs:', initRes.outputs);

// Subsequent call reuses the existing `page` and variables!
const extractRes = await kernel.browsers.repl(session.session_id, {
  code: `
    const links = await globalThis.page.$$eval('a', els => els.map(a => a.href));
    repl.write('Found ' + links.length + ' links');
  `,
});
```

CLI counterpart: `kernel browsers repl <session_id>` drives an interactive terminal directly into the VM.

When to use:
- Multi-step interactive workflows where initializing Playwright or downloading libraries on every step is prohibitive
- Co-located agents (such as running coding agents inside the browser VM alongside Chromium)
- Inspecting page state dynamically with `repl.help()` and `repl.write()`

## Surface 6 — WebMCP (Model Context Protocol)

WebMCP bridges web page actions and CDP tools into Model Context Protocol tools that LLMs can discover and invoke naturally.

```ts
// 1. Discover tools provided natively by the page (or registered polyfills)
const tools = await kernel.browsers.webmcp.listTools(session.session_id);
for (const tool of tools.tools) {
  console.log('Tool:', tool.tool_name, tool.description);
}

// 2. Invoke a discovered page tool
const result = await kernel.browsers.webmcp.invokeTool(session.session_id, {
  tool_ref: tools.tools[0].tool_ref,
  input: { query: 'laptop' },
});

// 3. Register custom tools backed by CDP or page evaluations
await kernel.browsers.webmcp.customTools.add(session.session_id, {
  namespace: 'custom',
  tools: [
    {
      name: 'get_cart_total',
      description: 'Reads current cart total from DOM',
      input_schema: { type: 'object', properties: {} },
    }
  ],
});
```

CLI counterpart: `kernel browsers webmcp custom-tools list|add|remove <session_id>`.

When to use:
- Websites exposing native AI agent interfaces via `navigator.modelContext`
- Declarative forms with `awaiting_submission` workflows
- Uniform tool contracts across complex web applications

## Surface 7 — Process Execution

Direct execution of shell commands, CLI utilities, and background processes inside the unikernel VM.

```ts
// Synchronous command execution
const execRes = await kernel.browsers.process.exec(session.session_id, {
  command: 'uname',
  args: ['-a'],
  timeout_ms: 10_000,
});
console.log('stdout:', execRes.stdout);

// Spawn a long-lived process or PTY
const proc = await kernel.browsers.process.spawn(session.session_id, {
  command: 'node',
  args: ['-e', 'console.log("running...")'],
});
```

CLI counterpart: `kernel browsers process <session_id>`.

When to use:
- Running local diagnostic or inspection tools in the VM
- Interacting with Linux filesystem utilities, measuring memory, or downloading files
- Executing standalone CLI tools co-located with the browser

## WebDriver BiDi

For Vibium, Selenium-style clients, or any other WebDriver BiDi consumer, use `session.webdriver_ws_url` in place of `cdp_ws_url`. Same lifecycle rules apply — `deleteByID` for cleanup.

## Mixing surfaces

You can use multiple surfaces in the same session — they all share the same browser VM and cookies. Common combinations:

- **Live view + computer-controls** — embed the live view URL in your UI, use `computer.*` to drive the browser based on screenshots.
- **CDP setup, `playwright.execute` for bulk** — connect once, use Playwright for navigation, switch to in-VM execute for tight extraction loops.
- **CDP + `browsers.curl`** — drive the page with Playwright, hit JSON endpoints from inside the browser's TLS fingerprint without spawning a new context.
