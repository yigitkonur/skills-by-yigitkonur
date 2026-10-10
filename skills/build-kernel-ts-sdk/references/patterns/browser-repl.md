# Browser REPL & Code Mode Architecture

The Browser REPL is an in-VM stateful Node.js execution runtime co-located with Chromium inside Kernel microVMs. Introduced in `@onkernel/sdk@0.107.0` and `@onkernel/cli@0.47.0`, it provides high-throughput programmatic browser control with zero network latency between automation code and the browser DOM.

---

## 1. Core Architecture & Execution Model

Unlike traditional remote CDP connections where every command (click, evaluate, wait) pays a network roundtrip, the Browser REPL runs inside the browser container:

- **Persistent JavaScript State**: Evaluated as sequential ECMAScript module cells. Top-level variables (`var`, `let`, `const`), function declarations, classes, closures, and module imports persist across execution turns.
- **Session CUID2 (`repl_id`)**: A unique identifier tracks the REPL lifecycle. It remains identical across calls, recovers from syntax errors, and survives browser page reloads. A new `repl_id` is generated only if explicitly reset (`reset: true`), killed, or terminated on uncaught OOM.
- **Explicit Output Streaming**: Raw expression return values are not automatically serialized. To emit output back to the calling agent, use:
  - `repl.write(text)` (emits under channel `'write'`)
  - `console.log(...)` (emits under channel `'stdout'`)
  - `console.error(...)` (emits under channel `'stderr'`)
  - `repl.emitImage({ path })` (returns inline base64 image content)
- **Response Shape (`BrowserReplResult`)**:
  ```ts
  interface BrowserReplResult {
    repl_id: string;
    success: boolean;
    content?: Array<BrowserReplContent>; // { type: 'text', channel: 'write' | 'stdout' | 'stderr', text: string } | { type: 'image', mime_type: string, data_b64: string }
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

### Navigation & State
- `await gotoUrl(url: string, options?: { timeout?: number, waitUntil?: 'load' | 'domcontentloaded' | 'networkidle' })`
- `await pageInfo()`: Returns current URL, title, viewport dimensions, and tab ID.
- `await accessibilitySnapshot()`: Returns a compact, structured accessibility tree suitable for LLM reasoning.
- `await waitMs(ms: number)`
- `await waitForLoad(options?)`
- `await waitForElement(selector: string, options?: { timeout?: number, state?: 'attached' | 'visible' })`
- `await waitForNetworkIdle(options?: { timeout?: number, idleTime?: number })`

### User Interaction
- `await click(target: string | { x: number, y: number })`: Clicks a CSS selector or coordinates.
- `await fillInput(selector: string, text: string)`: Clears and types text into input fields.
- `await typeText(text: string)`: Sends keystrokes to the focused element.
- `await pressKey(key: string)`: Sends special keys (e.g., `'Enter'`, `'Tab'`, `'Escape'`).
- `await scroll(options: { x?: number, y?: number, deltaX?: number, deltaY?: number })`

### DOM & Execution Escape Hatches
- `await js(fn: Function | string, options?: { arg?: any, targetId?: string })`: Evaluates code in page context; returns JSON-serializable output.
- `await cdp.send(method: string, params?: object)`: Direct CDP command bypass.
- `await captureScreenshot(path?: string)`: Saves PNG screenshot to VM filesystem.
- `await httpGet(url: string)`: In-VM HTTP fetch using the browser's proxy and network routing.

### Tab Management
- `await listTabs()`
- `await currentTab()`
- `await switchTab(tabId: string)`
- `await newTab(url?: string)`
- `await closeTab(tabId?: string)`
- `await ensureRealTab()`: Verifies the browser is not parked on `about:blank`.

---

## 3. Pre-Installed Libraries & Dynamic Imports

The microVM comes with stealth-hardened Playwright libraries pre-installed:
- `patchright`: Hardened anti-detection Playwright distribution.
- `playwright-core`: Standard Playwright engine.

```javascript
// Connect Playwright inside the REPL in one line
var playwright = await import('patchright');
var pwBrowser = await playwright.chromium.connectOverCDP(process.env.CDP_ENDPOINT);
var context = pwBrowser.contexts()[0];
var page = context.pages()[0];
```

To install and import external npm modules on demand:
```bash
# From local machine via Kernel CLI
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
await gotoUrl('https://news.ycombinator.com', { waitUntil: 'domcontentloaded' });
await waitForElement('.athing', { timeout: 5000 });

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

const result = await kernel.browsers.repl(sessionId, {
  code: script,
  timeout_sec: 15,
});

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
```
