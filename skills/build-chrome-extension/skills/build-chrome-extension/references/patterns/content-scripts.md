# Content Script Patterns (Manifest V3)

## Injection Methods

### 1. Static Declaration (manifest.json)

```jsonc
{
  "content_scripts": [{
    "matches": ["https://*.example.com/*"],
    "exclude_matches": ["https://admin.example.com/*"],
    "js": ["content-scripts/main.js"],
    "css": ["content-scripts/styles.css"],
    "run_at": "document_idle",
    "world": "ISOLATED"
  }]
}
```

### 2. Dynamic Injection (chrome.scripting)

Requires `"scripting"` permission. Injected from the service worker.

```typescript
// Inject file into a specific tab
await chrome.scripting.executeScript({
  target: { tabId: tab.id },
  files: ["content-scripts/injected.js"],
});

// Inject inline function with arguments
await chrome.scripting.executeScript({
  target: { tabId: tab.id },
  func: (selector: string, color: string) => {
    const el = document.querySelector(selector);
    if (el instanceof HTMLElement) el.style.backgroundColor = color;
  },
  args: ["#header", "yellow"],
});

// Inject into all frames
await chrome.scripting.executeScript({
  target: { tabId: tab.id, allFrames: true },
  files: ["content-scripts/all-frames.js"],
});
```

### 3. Dynamic Content Script Registration (persistent)

Unlike one-shot `executeScript`, these survive SW restarts:

```typescript
await chrome.scripting.registerContentScripts([{
  id: "my-dynamic-script",
  matches: ["https://*.example.com/*"],
  js: ["content-scripts/dynamic.js"],
  runAt: "document_idle",
  persistAcrossSessions: true,
}]);

// Update, unregister, list
await chrome.scripting.updateContentScripts([{ id: "my-dynamic-script", matches: ["https://*.newdomain.com/*"] }]);
await chrome.scripting.unregisterContentScripts({ ids: ["my-dynamic-script"] });
const scripts = await chrome.scripting.getRegisteredContentScripts();
```

## Execution Worlds: ISOLATED vs MAIN

| | ISOLATED (default) | MAIN |
|---|---|---|
| DOM access | Yes | Yes |
| Page JS variables | No | Yes |
| `chrome.*` APIs | Yes | **No** |
| Use case | Most content scripts | Intercepting page APIs |

```typescript
// MAIN world — manifest
{ "content_scripts": [{ "matches": ["*://*/*"], "js": ["main-world.js"], "world": "MAIN", "run_at": "document_start" }] }

// MAIN world — dynamic
await chrome.scripting.executeScript({
  target: { tabId: tab.id },
  func: () => { console.log(window.myApp); /* page vars accessible */ },
  world: "MAIN",
});
```

### When to use MAIN world

| Use case | Why |
|---|---|
| Access page JS variables | ISOLATED cannot see them |
| Intercept `fetch` / `XMLHttpRequest` | Must monkey-patch the page's global |
| Read framework state (React, Vue) | State lives in page JS context |
| Intercept WebSocket messages | Must wrap page's `WebSocket` constructor |

### MAIN world: intercepting fetch

```typescript
// Runs in MAIN world
const originalFetch = window.fetch;
window.fetch = async function (...args: Parameters<typeof fetch>) {
  const response = await originalFetch.apply(this, args);
  const url = typeof args[0] === "string" ? args[0] : (args[0] as Request).url;
  if (url.includes("/api/data")) {
    const body = await response.clone().json();
    window.dispatchEvent(new CustomEvent("__ext_intercepted", { detail: { url, body } }));
  }
  return response;
};
```

## Communication Patterns

### Content script <-> service worker

```typescript
// content-script.ts — one-shot
const response = await chrome.runtime.sendMessage({ type: "get-settings", key: "theme" });

// content-script.ts — long-lived port
const port = chrome.runtime.connect({ name: "stream" });
port.postMessage({ type: "subscribe", channel: "updates" });
port.onMessage.addListener((msg) => console.log("Received:", msg));
```

### ISOLATED <-> MAIN world bridging

Both worlds share the DOM, so use `CustomEvent` or `window.postMessage`:

```typescript
// MAIN world → ISOLATED world
window.dispatchEvent(new CustomEvent("__ext_data", {
  detail: { user: window.__APP_STATE__.user },
}));

// ISOLATED world — receive
window.addEventListener("__ext_data", ((event: CustomEvent) => {
  chrome.runtime.sendMessage({ type: "page-data", data: event.detail });
}) as EventListener);
```

```typescript
// Alternative: window.postMessage
// MAIN world
window.postMessage({ source: "ext-main", payload: { key: "value" } }, "*");

// ISOLATED world — always validate source
window.addEventListener("message", (event) => {
  if (event.source !== window || event.data?.source !== "ext-main") return;
  chrome.runtime.sendMessage({ type: "from-page", payload: event.data.payload });
});
```

## Shadow DOM Isolation for UI Injection

Inject extension UI without CSS conflicts:

```typescript
function injectExtensionUI(): void {
  if (document.getElementById("my-ext-root")) return; // idempotent guard

  const host = document.createElement("div");
  host.id = "my-ext-root";
  const shadow = host.attachShadow({ mode: "closed" });

  const style = document.createElement("style");
  style.textContent = `
    :host { all: initial; position: fixed; bottom: 16px; right: 16px;
            z-index: 2147483647; font-family: system-ui, sans-serif; }
    .panel { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px;
             padding: 16px; width: 320px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    button { background: #4285f4; color: white; border: none;
             padding: 8px 16px; border-radius: 4px; cursor: pointer; }
  `;

  const panel = document.createElement("div");
  panel.className = "panel";
  panel.innerHTML = `<h3>My Extension</h3><button id="ext-btn">Click</button>`;

  shadow.append(style, panel);
  document.body.appendChild(host);

  shadow.getElementById("ext-btn")!.addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "ui-action" });
  });
}
```

## Making Content Scripts Idempotent

Guard against re-injection (dynamic injection, SPA nav, extension reload):

```typescript
// Flag guard — top of content script
if ((window as any).__MY_EXT_INJECTED) { /* already running */ }
else { (window as any).__MY_EXT_INJECTED = true; init(); }

// DOM element guard
function ensureSidebar(): HTMLElement {
  let el = document.getElementById("ext-sidebar");
  if (!el) { el = document.createElement("div"); el.id = "ext-sidebar"; document.body.appendChild(el); }
  return el;
}
```

## CSS Injection Patterns

```typescript
// From service worker — file-based
await chrome.scripting.insertCSS({ target: { tabId: tab.id }, files: ["styles/highlight.css"] });

// Inline CSS
await chrome.scripting.insertCSS({ target: { tabId: tab.id }, css: "body { border: 3px solid red !important; }" });

// Remove previously inserted CSS
await chrome.scripting.removeCSS({ target: { tabId: tab.id }, files: ["styles/highlight.css"] });
```

### Adopted Stylesheets (modern, performant, for shadow DOM)

```typescript
const sheet = new CSSStyleSheet();
sheet.replaceSync(`.ext-highlight { background: yellow; }`);
const shadow = host.attachShadow({ mode: "closed" });
shadow.adoptedStyleSheets = [sheet];
```

## Content Script Lifecycle and Cleanup

Destroyed when: tab closes, navigation to different page, extension reload/update.

```typescript
const controller = new AbortController();
const observer = new MutationObserver(handleMutations);
observer.observe(document.body, { childList: true, subtree: true });

window.addEventListener("message", (e) => { /* ... */ }, { signal: controller.signal });
window.addEventListener("beforeunload", () => { controller.abort(); observer.disconnect(); });

// Also detect extension unload
chrome.runtime.onConnect.addListener((port) => {
  port.onDisconnect.addListener(() => { controller.abort(); observer.disconnect(); });
});
```

## match_patterns Syntax Reference

| Pattern | Matches |
|---|---|
| `https://*.example.com/*` | Any path on example.com + subdomains, HTTPS |
| `https://example.com/path/*` | Paths starting with `/path/` |
| `*://*.example.com/*` | HTTP and HTTPS |
| `<all_urls>` | All HTTP(S), file, ftp (triggers extra CWS review) |
| `https://example.com/` | Exact root path only |
| `http://127.0.0.1/*` | Localhost HTTP |

**Rules:** scheme is `http`/`https`/`file`/`ftp`/`*`; host wildcard `*` only at start (`*.example.com`); path `*` matches any chars including `/`.

| Invalid pattern | Why |
|---|---|
| `https://www.example.com` | Missing path — need at least `/` |
| `https://*example.com/*` | `*` must be followed by `.` or stand alone |
| `https://foo.*.com/*` | Wildcard only at start of host |

## run_at Options

| Value | When | Use case |
|---|---|---|
| `document_start` | After CSS, before DOM or page scripts | Block/modify page scripts, MAIN world overrides |
| `document_end` | DOM parsed (≈DOMContentLoaded), subresources loading | Most common — DOM ready, safe to `querySelector` |
| `document_idle` | After `document_end`, page idle | **Default.** Non-urgent; does not slow page load |

### document_start pitfall: no `document.body` yet

```typescript
if (document.body) { injectUI(); }
else {
  const obs = new MutationObserver(() => {
    if (document.body) { obs.disconnect(); injectUI(); }
  });
  obs.observe(document.documentElement, { childList: true });
}
```

## Accessing Extension Resources

```typescript
const iconUrl = chrome.runtime.getURL("images/icon.png");
const img = document.createElement("img");
img.src = iconUrl;
```

Must declare in manifest:

```jsonc
{
  "web_accessible_resources": [{
    "resources": ["images/*", "styles/*", "injected.js"],
    "matches": ["https://*.example.com/*"]
  }]
}
```

Only expose the minimum necessary. Exposed resources let websites detect your extension.

## Common Content Script Pitfalls

| Pitfall | What happens | Fix |
|---|---|---|
| Not handling SPA navigation | Script runs once; new views missed | `MutationObserver` or `popstate`/`hashchange` |
| CSS leaking into page | Extension styles break page layout | Shadow DOM or unique-prefix selectors |
| Page CSS affecting extension UI | `* { margin: 0 }` breaks your panel | Shadow DOM with `:host { all: initial }` |
| `chrome.*` in MAIN world | `chrome.runtime` is `undefined` | Bridge via CustomEvent to ISOLATED world |
| `querySelector` returns null | NPE crash | Always null-check |
| `window.onload` at `document_idle` | Already fired — never runs | Check `document.readyState` |
| No cleanup on navigation | Observers and intervals leak | `AbortController` + `beforeunload` |
| Injecting large frameworks | Bloats page, slows it down | Keep content scripts minimal |
| CSP blocks inline scripts | `script.textContent = ...` fails | Use files via `web_accessible_resources` |
| Multiple injection (no guard) | Duplicate UI, duplicate listeners | Check sentinel flag before running |
| Race with page scripts | Page modifies DOM after your changes | `MutationObserver` for reactive updates |
