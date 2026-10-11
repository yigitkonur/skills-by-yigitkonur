# Browser control surfaces

Kernel exposes a Chromium browser in a unikernel VM. Seven surfaces plus WebDriver BiDi drive it. Pick the right surface for your workload — mixing surfaces in the same session is supported because they all share the same browser VM and session state.

Kernel's own guidance: `playwright.execute` is the default when you know the page steps; computer controls are the recommended fallback (and the stronger option on aggressive-detection sites, because they open no CDP connection); WebMCP when the site registers tools; the REPL when an agent writes reusable helpers; raw CDP when you already have a Playwright/Puppeteer suite (it adds a protocol fingerprint and a network hop).

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
│   └─► `kernel.browsers.curl(id, { url })` (small, buffered) or `kernel.browsers.fetch(id, url)` (streaming/large)
├── WebDriver BiDi client (Vibium etc.)
│   └─► Pass `session.webdriver_ws_url` instead of CDP
├── Persistent interactive Node.js scripting in VM across calls
│   └─► Browser REPL via `kernel.browsers.repl(id, ...)` or `kernel browsers repl`
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
  timeout_sec: 60,                            // default 60, max 300 (keep the client timeout above it, see client-and-config.md)
  executor: 'worker-1',                       // named persistent executor (up to 8 processes)
});

// Response is { success, error?, result, stderr, stdout, tab?: { target_id, created } }
if (!res.success) throw new Error(`playwright.execute failed: ${res.error}`);
const { title, links } = res.result as { title: string; links: string[] };

// Manage named executors (CLI: kernel browsers playwright executors list|delete <id>)
const execList = await kernel.browsers.playwright.executors.list(session.session_id);
await kernel.browsers.playwright.executors.delete('worker-1', { id_or_name: session.session_id, close_tab: true });
```

When to use:

- Bulk extraction or scripted multi-step operations
- Anywhere CDP latency adds up — the script runs in the browser VM with `page`, `context`, `browser`, and `webmcp` (browser-wide WebMCP helper) already in scope; Patchright is the default engine
- Returning structured results without serialising every value over CDP
- Accessibility snapshot for agents: `return await page.ariaSnapshot({ mode: 'ai' })` yields a ref-based YAML tree; act on a node later with `page.locator('aria-ref=f1e3')`

Executors: calls on one executor run in order, different executors run concurrently and fail independently; the default executor binds `page` to the active tab, a named executor (`^[A-Za-z0-9_-]{1,64}$`) owns a background tab it opens on first use. A ninth named executor returns `409` listing the current ones; delete finished executors (deleting `default` restarts it). Named executors are not removed automatically while the browser runs (only at shutdown), so delete the ones you are done with.

Caveats:

- The code body is a string; pass closures' values via JSON-encoded environment variables or via the response shape, not via JavaScript closures from your service.
- The VM has no access to `process.env` from your service. If the script needs an API key, pass it in the code body literal or fetch it from inside the VM.
- Stack traces are returned as strings; budget for plaintext debugging.

## Surface 3 — Computer controls

```ts
// Screenshot returns a raw Response — wire to a VLM directly. Optional { region: { x, y, width, height } }.
// Faster than CDP Page.captureScreenshot (no CDP hop).
const resp = await kernel.browsers.computer.captureScreenshot(session.session_id);
const png = Buffer.from(await resp.arrayBuffer());

// Mouse. clickMouse: button 'left'|'right'|'middle'|'back'|'forward', click_type 'down'|'up'|'click',
// num_clicks, hold_keys (modifiers).
await kernel.browsers.computer.clickMouse(session.session_id, { x: 100, y: 200, button: 'left' });
// moveMouse and dragMouse follow human-like Bezier paths by default (smooth: true);
// duration_ms: moveMouse 50-5000, dragMouse 50-10000; smooth: false -> instant move / linear drag
// (dragMouse steps_per_segment default 10, step_delay_ms default 50, ignored when smooth is true).
await kernel.browsers.computer.moveMouse(session.session_id, { x: 400, y: 300, duration_ms: 800 });
// dragMouse takes an ordered path of [x, y] pairs (>= 2 points)
await kernel.browsers.computer.dragMouse(session.session_id, {
  path: [[100, 100], [300, 300]],
});
const pos = await kernel.browsers.computer.getMousePosition(session.session_id); // { x, y }

// Keyboard
await kernel.browsers.computer.typeText(session.session_id, {
  text: 'hello world',        // default typing is human-like (variable timing)
});
// `delay` (ms between keystrokes) only applies when smooth typing is off. The docs add
// `smooth: false` and `typo_chance` (0-0.10) for typeText; they are NOT in @onkernel/sdk@0.123.0
// types (nor CLI 0.47.0), so `{ text, smooth: false }` is a TS error until the SDK ships them.
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
    { type: 'press_key',    press_key:    { keys: ['Return'] } },
    { type: 'sleep',        sleep:        { duration_ms: 250 } },     // pause between actions
    { type: 'set_cursor',   set_cursor:   { hidden: true } },         // hide cursor for clean screenshots
  ],
});
```

When to use:

- Vision-loop agents (Claude computer-use, OpenAI computer-use, custom VLM). They sit on the same VM display, so they can see native dialogs, canvas, iframes, and PDFs
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

Response: `{ status, headers (string[] per name), body, duration_ms }`; `url` must be http(s); `method` is one of GET|HEAD|POST|PUT|PATCH|DELETE|OPTIONS. `curl` buffers the **whole** body inside the browser process, so a large or unknown-size response can OOM the VM. Use `kernel.browsers.fetch` for those:

```ts
// Streams the body; only works for a session this client created/retrieved/listed (route cache), else KernelError.
const streamed: Response = await kernel.browsers.fetch(session.session_id, 'https://example.com/big.zip', { method: 'GET' });
```

Response `Set-Cookie` headers update the browser's cookie jar (and profile).

When to use:

- API calls from inside the browser's network stack (cookies, proxy, fingerprint all preserved)
- Bypassing CDP for non-DOM work
- Hitting endpoints that block standard `fetch` from your server

## Surface 5 — Persistent Browser REPL

A long-lived Node.js runtime inside the browser VM where top-level variables, bindings, closures, and imports persist across calls until explicitly reset. In-scope helpers (`gotoUrl`, `pageInfo`, `click`, `fillInput`, `js`) are pre-injected into the global scope. See `references/patterns/browser-repl.md`.

```ts
// Initial call navigates using in-scope REPL helpers or pre-installed patchright
const initRes = await kernel.browsers.repl(session.session_id, {
  code: `
    await gotoUrl('https://example.com');
    const info = await pageInfo();
    repl.write('Page loaded: ' + info.title);
  `,
  timeout_sec: 60,
});

// Response is `BrowserReplResult`:
// { repl_id, success, content?, content_truncated?, duration_ms?, error?, repl_terminated?, stack? }
console.log('REPL ID:', initRes.repl_id); // stable across calls until reset, timeout, crash/OOM, or API restart
for (const item of initRes.content ?? []) {
  if (item.type === 'text') {
    // item.channel: 'write' (from repl.write) | 'stdout' | 'stderr'
    console.log(`[${item.channel}] ${item.text}`);
  } else if (item.type === 'image') {
    console.log(`Image: ${item.mime_type} (${item.data_b64.length} b64 chars)`);
  }
}

// Subsequent call reuses existing state and variables!
const extractRes = await kernel.browsers.repl(session.session_id, {
  code: `
    const links = await js(() => Array.from(document.querySelectorAll('a')).map(a => a.href));
    repl.write('Found ' + links.length + ' links');
  `,
});
```

A call that exceeds `timeout_sec` (default 60, max 300) destroys the REPL: check `repl_terminated`; every top-level binding is then gone and the next call gets a new `repl_id`. The REPL is JavaScript only (no TypeScript, static `import`, top-level `return`) and is unrestricted code execution in the VM — never feed it page content or other untrusted input.

CLI counterpart: `kernel browsers repl <session_id>` executes code in the VM REPL.

When to use:
- Multi-step interactive workflows where initializing Playwright on every step is prohibitive
- Co-located coding agents running inside the browser VM
- Inspecting page state dynamically with in-VM `repl` helpers (`repl.write()`, `repl.emitImage()`, `repl.help()`)

## Surface 6 — WebMCP (Model Context Protocol)

WebMCP lets a site's registered tools (WebMCP is a W3C Web Machine Learning CG draft) be discovered and invoked instead of scraping the DOM. `listTools` returns a snapshot across every open tab and frame, including polyfill-registered and custom tools. See `references/patterns/webmcp.md`, including the no-retry rule for `invokeTool`.

```ts
// 1. Discover tools (query: { exclude_custom?: boolean })
const { tools } = await kernel.browsers.webmcp.listTools(session.session_id);
for (const item of tools) {
  console.log('Tool:', item.tool.name, item.tool.description, item.tool.inputSchema);
}

// 2. Invoke a discovered tool by tool_ref
const toolToInvoke = tools.find(t => t.tool.name === 'searchProducts');
if (toolToInvoke) {
  // Never retry an invocation: it can have side effects even if the response is lost.
  const result = await kernel.browsers.webmcp.invokeTool(
    session.session_id,
    { tool_ref: toolToInvoke.tool_ref, input: { query: 'laptop' }, timeout_sec: 30 }, // 1-120, default 60
    { maxRetries: 0 },
  );
  console.log('Status:', result.status, 'Output:', result.output);
}
```

```ts
// List or remove custom tools:
const customList = await kernel.browsers.webmcp.customTools.list(session.session_id);
// Note: remove takes tool ID as 1st arg, browser id_or_name in params:
await kernel.browsers.webmcp.customTools.remove(customList.tools[0].id, {
  id_or_name: session.session_id,
});
```

CLI counterpart:
```bash
kernel browsers webmcp list <session_id>
kernel browsers webmcp invoke <session_id> --tool-ref <ref> --input '{"query":"laptop"}'
kernel browsers webmcp custom-tools list|add|remove <session_id>
```

When to use:
- Websites that register WebMCP tools (native or `navigator.modelContext` polyfill)
- Exposing DOM extraction or CDP actions to agent LLMs with strict JSON schemas
- Uniform tool contracts across complex web applications

## Surface 7 — Process Execution

Direct execution of shell commands, CLI utilities, and background processes inside the unikernel VM.

```ts
// 1. Synchronous command execution
// Response: { exit_code?: number, stdout_b64?: string, stderr_b64?: string, duration_ms?: number }
const execRes = await kernel.browsers.process.exec(session.session_id, {
  command: 'uname',
  args: ['-a'],
  timeout_sec: 10,
  // as_root: false,
  // env: { FOO: 'bar' },
  // cwd: '/tmp',
});
const stdout = Buffer.from(execRes.stdout_b64 ?? '', 'base64').toString('utf8');
console.log('stdout:', stdout);

// 2. Spawn long-lived background process or PTY
const proc = await kernel.browsers.process.spawn(session.session_id, {
  command: 'node',
  args: ['-e', 'console.log("running...")'],
  allocate_tty: false,                        // allocate pseudo-terminal
});
if (proc.process_id) {
  const status = await kernel.browsers.process.status(proc.process_id, { id_or_name: session.session_id });
  await kernel.browsers.process.kill(proc.process_id, { id_or_name: session.session_id, signal: 'TERM' });
}
```

Also available: `process.stdin(pid, { id_or_name, data_b64 })`, `process.stdoutStream(pid, { id_or_name })` (SSE `{ stream, data_b64 }`, final `{ event: 'exit', exit_code }`), `process.resize(pid, { id_or_name, cols, rows })` (PTY processes only). `process.status` reports `mem_bytes` only for processes started with `spawn` and no CPU. The VM already listens on 8080, 9222-9225, 8888, 10001, 10002; pick other ports for servers you spawn.

CLI counterpart: `kernel browsers process exec <session_id> -- uname -a` (trailing args run via `/bin/bash -c`) or `--command uname --args -a`; `--args` values are split on commas, so use the SDK for commas inside a `sh -c` string.

When to use:
- Running local diagnostic or inspection tools in the VM (e.g. measuring memory via `free -m`)
- Interacting with Linux filesystem utilities or downloading binaries
- Executing standalone CLI tools co-located with the browser

## Lower-level access: SSH

`kernel browsers ssh <session_id>` opens a shell in the VM (needs `websocat` locally; ephemeral ed25519 key unless `-i`), with `-L`/`-R` port forwarding, e.g. `-R 3000:localhost:3000` exposes a local dev server to the remote browser. SSH is not browser activity: set `--timeout` on create or keep live view open. `--setup-only` configures SSH and prints the connection command.

## WebDriver BiDi

For Vibium, Selenium-style clients, or any other WebDriver BiDi consumer, use `session.webdriver_ws_url` in place of `cdp_ws_url`. Same lifecycle rules apply — `deleteByID` for cleanup.

## Mixing surfaces

You can use multiple surfaces in the same session — they all share the same browser VM and cookies. Common combinations:

- **Live view + computer-controls** — embed the live view URL in your UI, use `computer.*` to drive the browser based on screenshots.
- **CDP setup, `playwright.execute` for bulk** — connect once, use Playwright for navigation, switch to in-VM execute for tight extraction loops.
- **CDP + `browsers.curl`** — drive the page with Playwright, hit JSON endpoints from inside the browser's TLS fingerprint without spawning a new context.
