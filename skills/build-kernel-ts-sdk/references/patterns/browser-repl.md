# Browser REPL & Code Mode Architecture

The Browser REPL is an in-VM stateful Node.js execution runtime co-located with Chromium inside Kernel microVMs. Available in the SDK since `@onkernel/sdk@0.107.0` (CLI since 0.38.2), it provides high-throughput programmatic browser control with zero network latency between automation code and the browser DOM.

---

## 1. Core Architecture & Execution Model

Unlike traditional remote CDP connections where every command (click, evaluate, wait) pays a network roundtrip, the Browser REPL runs inside the browser container:

- **Persistent JavaScript State**: Evaluated as sequential ECMAScript module cells. Top-level variables (`var`, `let`, `const`), function declarations, classes, closures, and module imports persist across execution turns.
- **Session CUID2 (`repl_id`)**: A unique identifier tracks the REPL lifecycle. State and `repl_id` survive successful calls, syntax errors and ordinary exceptions, and Chromium restarts (the browser reconnects lazily). They are destroyed, and the next call starts a fresh REPL with a new `repl_id`, on: explicit `reset: true`, **execution timeout** (`timeout_sec`, default 60, max 300), crash/OOM/uncaught asynchronous exception/protocol corruption, or API restart. Check `repl_terminated` after every call; when true, every top-level binding is gone.
- **Language**: JavaScript only. TypeScript, static `import`/`export`, and top-level `return` are rejected; top-level `await` and dynamic `import()` work. `code` may be empty only with `reset: true`. Calls are serialized.
- **Security**: unrestricted code execution inside the browser VM (Node built-ins, files, env vars, processes, network, raw CDP), not a sandbox. Never send page content, tool output, or other untrusted input as `code`.
- **Explicit Output Streaming**: Raw expression return values are not automatically serialized. To emit output back to the calling agent, use:
  - `repl.write(text)` (emits under channel `'write'`)
  - `console.log(...)` (emits under channel `'stdout'`)
  - `console.error(...)` (emits under channel `'stderr'`)
  - `repl.emitImage({ path })` (returns inline base64 image content)
- **Response Shape (`BrowserReplResult`)**:
  ```ts
  type BrowserReplContent =
    | { type: 'text'; channel: 'write' | 'stdout' | 'stderr'; text: string }
    | { type: 'image'; mime_type: string; data_b64: string };

  interface BrowserReplResult {
    repl_id: string;
    success: boolean;
    content?: Array<BrowserReplContent>;
    content_truncated?: boolean;
    duration_ms?: number;
    error?: string;
    repl_terminated?: boolean;
    stack?: string;
  }
  ```

---

## 2. In-VM Globals & Helper Library

The REPL environment automatically injects pre-bound async helper functions into the global scope (also mirrored under the frozen `browser` namespace):

Helper names (all documented): navigation/state `gotoUrl`, `pageInfo`, `accessibilitySnapshot`, `waitMs`, `waitForLoad`, `waitForElement`, `waitForNetworkIdle`, `waitForEvent`; interaction `click`, `fillInput`, `typeText`, `pressKey`, `scroll`; page evaluation `js`; tabs `listTabs`, `currentTab`, `switchTab`, `newTab`, `closeTab`, `ensureRealTab`, `iframeTarget`; escape hatches `cdp`, `drainEvents`, `captureScreenshot`, `uploadFile`, `httpGet`. Call `repl.help()` for the index and `repl.help("click")` for one helper's exact signature; the signatures below are the ones Kernel's docs or MCP tool description show.

### Navigation & State
- `await gotoUrl(url)` and `click(...)` do not wait for the resulting page state. Follow `gotoUrl` with `await waitForLoad()` before reading or snapshotting.
- `await waitForElement(selector, { state: 'visible', timeoutSec: 15 })`: returns truthy when found, falsy on timeout (it does not throw; check the result). The option is `timeoutSec`, not `timeout`.
- `await accessibilitySnapshot()`: compact projection of the computed accessibility tree (`snapshot.nodes` with `role`, `name`, ...). Nodes can be passed straight to `click`, `fillInput`, `waitForElement`, and `uploadFile`; backend node ids go stale after navigation, so re-snapshot after state changes.
- `await waitForEvent(...)`: pre-arm it before an action when the event could fire before the action returns.

### User Interaction
- `await click(selector | node | { x, y })`: selector and node clicks wait for a visible, enabled, stable, unobscured target, scroll it into view, and dispatch physical mouse input; `{ x, y }` is a raw coordinate click.
- `await fillInput(selector, text)`, `typeText(text)`, `pressKey('Enter')`, `scroll(...)`.

### DOM & Execution Escape Hatches
- `await js(fn, { arg, targetId })`: evaluates page JavaScript exactly once; returns JSON-serializable values only (DOMRects come back empty, so copy `x, y, width, height`); page functions do not capture REPL bindings, pass data through `arg`.
- `await cdp(method, params, sessionId)`: raw CDP; pass `null` as the session for browser-level `Target.*` commands and the returned `sessionId` for page-level commands.
- `await captureScreenshot('/tmp/page.png')` returns the VM-local path; call `await repl.emitImage({ path })` to return it.
- `await httpGet(url)`: in-VM HTTP GET that returns the response body, with no page navigation (the docs parse it with a package such as cheerio). The docs do not say whether it uses the browser's proxy or network routing.
- `await iframeTarget('checkout.example')`: cross-origin frame as its own CDP target, then `js(fn, { targetId: frame.targetId })`.

### Tab Management
`listTabs`, `currentTab`, `switchTab`, `newTab`, `closeTab`, `ensureRealTab` (all awaited; see `repl.help("switchTab")` for arguments).

---

## 3. Pre-Installed Libraries & Dynamic Imports

The VM ships lockfile-pinned Playwright packages (no extra browser download):
- `patchright`: Hardened anti-detection Playwright distribution.
- `playwright-core`: Standard Playwright engine.

```javascript
// Connect Playwright inside the REPL in one line
var playwright = await import('patchright');
var pwBrowser = await playwright.chromium.connectOverCDP(process.env.CDP_ENDPOINT);
var pwContext = pwBrowser.contexts()[0];
var pwPage = pwContext.pages()[0] ?? await pwContext.newPage();
```

To install and import external npm modules on demand:
```bash
# From local machine via Kernel CLI (if the registry fails with UNABLE_TO_VERIFY_LEAF_SIGNATURE,
# set NODE_OPTIONS=--use-openssl-ca as an env var on the install command)
kernel browsers process exec <session-id> -- npm install -g cheerio
```
```javascript
// Inside subsequent REPL execution cell
var cheerio = await import('cheerio');
```

---

## 4. The Code Mode Agent Pattern

Code Mode unifies all browser interaction into a single tool call (`browser_repl`), replacing noisy multi-turn tool calling with compact programs:

```ts
import Kernel from '@onkernel/sdk';

const kernel = new Kernel();

// Example: Single-turn data extraction script with retries and assertions
const script = `
await gotoUrl('https://news.ycombinator.com');
await waitForLoad();
if (!await waitForElement('.athing', { timeoutSec: 5 })) throw new Error('.athing not found');

var headlines = await js(() => {
  return Array.from(document.querySelectorAll('.athing')).slice(0, 5).map(row => {
    const titleEl = row.querySelector('.titleline > a');
    return {
      title: titleEl?.textContent || '',
      url: titleEl?.href || ''
    };
  });
});

repl.write(JSON.stringify(headlines, null, 2));
`;

// timeout_sec bounds the cell (default 60, max 300); exceeding it destroys the REPL and all bindings.
// Keep the client timeout above it and do not retry: a retry can repeat clicks and form submits.
const result = await kernel.browsers.repl(
  sessionId,
  { code: script, timeout_sec: 15 },
  { timeout: 30_000, maxRetries: 0 },
);

if (result.repl_terminated) {
  // all top-level bindings from earlier calls are gone; re-declare helpers
}

if (result.success) {
  const output = result.content?.find(c => c.type === 'text' && c.channel === 'write');
  if (output && output.type === 'text') {
    console.log('Headlines:', JSON.parse(output.text || '[]'));
  }
} else {
  console.error('REPL Error:', result.error);
}
```

---

## 5. CLI Reference (`@onkernel/cli@0.47.0`)

```bash
# In-VM Browser REPL (code passed as positional argument or piped via stdin)
kernel browsers repl <session-id>
kernel browsers repl <session-id> "await gotoUrl('https://example.com'); repl.write(await pageInfo());"

# Pipe a multi-line script file via stdin
cat ./agent-step.js | kernel browsers repl <session-id>

# Reset REPL state before running code
kernel browsers repl <session-id> "var freshState = 123;" --reset --timeout-sec 30

# Save images emitted by repl.emitImage(...) locally
kernel browsers repl <session-id> --image-dir ./shots "await repl.emitImage({ path: await captureScreenshot('/tmp/p.png') })"
```

Through the Kernel MCP `browser_repl` tool a single call is capped at 150 s; the API/SDK allows up to 300 s. Do not let a harness or HTTP client retry a cell after a timeout or dropped connection.
