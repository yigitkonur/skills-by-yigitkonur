# Chrome Extension Debugging Guide (Manifest V3)

## Debugging Contexts Overview

Chrome extensions run across multiple isolated contexts. Each requires a different debugging approach.

| Context | Where It Runs | How to Open DevTools | Persists? |
|---------|--------------|---------------------|-----------|
| Service worker (background) | Isolated V8 worker thread | `chrome://extensions` → "Inspect views: service worker" | No — terminates on idle |
| Popup | Extension popup window | Right-click popup → "Inspect" | No — closes with popup |
| Options page | Extension tab | Normal DevTools (F12) | Yes |
| Content script | Injected into web page | Page DevTools → Sources → Content Scripts | While page is open |
| Side panel | Extension side panel | Right-click panel → "Inspect" | While panel is open |
| Offscreen document | Hidden DOM document | `chrome://extensions` may list it | While document exists |

---

## Debugging the Service Worker

### chrome://extensions Page

1. Navigate to `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Find your extension card
4. Click **"service worker"** link under "Inspect views"
5. This opens a dedicated DevTools window for the service worker

### chrome://serviceworker-internals

Navigate to `chrome://serviceworker-internals` to see all registered service workers:
- View registration status
- Force-stop a service worker to test restart resilience
- Check for registration errors
- View the scope and script URL

### Key Debugging Patterns

```typescript
// background.ts — structured logging for service worker lifecycle
chrome.runtime.onInstalled.addListener((details) => {
  console.log("[SW] onInstalled:", details.reason, details.previousVersion);
});

chrome.runtime.onStartup.addListener(() => {
  console.log("[SW] onStartup — browser cold start");
});

// Log when the service worker activates
console.log("[SW] Script evaluated at", new Date().toISOString());

// Track unexpected terminations by setting an alarm
chrome.alarms.create("heartbeat", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "heartbeat") {
    console.log("[SW] Heartbeat at", new Date().toISOString());
  }
});
```

---

## Inspecting the Popup

1. Click the extension icon to open the popup
2. **Right-click** anywhere inside the popup
3. Select **"Inspect"** from the context menu
4. DevTools opens attached to the popup

**Critical:** The popup closes when it loses focus. The DevTools window keeps it alive. If you close DevTools, the popup closes too.

**Tip:** During development, open your popup as a full tab instead:

```typescript
// Open the configured popup path in a tab for easier debugging
const popupPath = chrome.runtime.getManifest().action?.default_popup;
if (popupPath) {
  const popupUrl = chrome.runtime.getURL(popupPath);
  chrome.tabs.create({ url: popupUrl });
}
```

---

## Inspecting Content Scripts

1. Open DevTools on the target web page (F12 or Ctrl+Shift+I)
2. Go to **Sources** tab
3. In the left panel, expand **Content Scripts**
4. Find your extension's scripts under its name/ID
5. Set breakpoints, inspect variables, step through code

### Console Context Selector

The DevTools console defaults to the **top** (page) context. To evaluate expressions in your content script's world:
- Click the context dropdown (shows "top") above the console
- Select your extension's content script context
- Now `chrome.runtime.sendMessage(...)` etc. work in the console

---

## Common Error Messages

| Error Message | Cause | Fix |
|--------------|-------|-----|
| `Uncaught Error: Extension context invalidated` | Extension was reloaded/updated while content script was running | Guard with `chrome.runtime?.id` check before API calls |
| `Could not establish connection. Receiving end does not exist.` | No listener for `chrome.runtime.onMessage` in the target context, or target context is not running | Ensure the service worker is alive; add error handling to `sendMessage` |
| `Error in event handler: TypeError: Cannot read properties of undefined` | Chrome API returned unexpected shape or callback error | Check `chrome.runtime.lastError` in callbacks; use try-catch in async |
| `Manifest file is missing or unreadable` | Invalid JSON in `manifest.json` | Validate JSON syntax; check for trailing commas |
| `'content_scripts[0].matches' is missing or invalid` | Match pattern syntax error | Use valid patterns: `"https://*/*"`, `"*://*.example.com/*"` |
| `Permissions are not allowed for the extension` | Invalid permission string in manifest | Check [permissions list](https://developer.chrome.com/docs/extensions/reference/permissions-list) |
| `Service worker registration failed` | Syntax error in service worker file, or import error | Check for top-level errors; ensure all imports use `import` not `require` |
| `Refused to execute inline script because it violates CSP` | Inline `<script>` in popup/options HTML | Move all JS to external files; update `content_security_policy` in manifest |
| `Access to fetch at '...' from origin 'chrome-extension://...' has been blocked by CORS` | Server does not allow extension origin | Add domain to `host_permissions` in manifest; the browser attaches CORS bypass for listed hosts |
| `chrome.scripting.executeScript: Cannot access a chrome:// URL` | Trying to inject into a restricted page | Skip `chrome://`, `chrome-extension://`, `edge://`, `about:` URLs |
| `Quota exceeded for storage.sync` | Exceeded 8KB per item or 100KB total for sync storage | Switch to `storage.local` (10MB limit) or chunk data |
| `The message port closed before a response was received.` | Message handler did not return `true` for async response or did not call `sendResponse` | Return `true` from `onMessage` listener when using async `sendResponse` |
| `Unchecked runtime.lastError: The extensions gallery cannot be scripted.` | Trying to inject into Chrome Web Store | Filter out `chromewebstore.google.com` URLs |

---

## Console Logging Strategy

### Prefixed Logging Across Contexts

```typescript
// src/utils/logger.ts
type LogLevel = "debug" | "info" | "warn" | "error";

const CONTEXT_LABELS = {
  background: "[BG]",
  popup: "[POPUP]",
  content: "[CS]",
  options: "[OPT]",
  sidepanel: "[SP]",
} as const;

type Context = keyof typeof CONTEXT_LABELS;

export function createLogger(context: Context) {
  const prefix = CONTEXT_LABELS[context];

  return {
    debug: (...args: unknown[]) => console.debug(prefix, ...args),
    info: (...args: unknown[]) => console.info(prefix, ...args),
    warn: (...args: unknown[]) => console.warn(prefix, ...args),
    error: (...args: unknown[]) => console.error(prefix, ...args),
    table: (data: unknown) => {
      console.group(prefix);
      console.table(data);
      console.groupEnd();
    },
  };
}

// Usage in background.ts
const log = createLogger("background");
log.info("Service worker started");

// Usage in content-script.ts
const log = createLogger("content");
log.info("Content script injected on", window.location.href);
```

### Conditional Debug Logging

```typescript
// src/utils/debug.ts
const IS_DEV = !("update_url" in chrome.runtime.getManifest());

export const debug = {
  log: (...args: unknown[]) => {
    if (IS_DEV) console.log("[DEBUG]", ...args);
  },
  time: (label: string) => {
    if (IS_DEV) console.time(label);
  },
  timeEnd: (label: string) => {
    if (IS_DEV) console.timeEnd(label);
  },
};
```

**How it works:** Extensions installed from the Chrome Web Store have `update_url` in their manifest. Locally loaded extensions do not.

---

## Network Request Debugging

### From Service Worker

Service worker network requests appear in the **service worker DevTools** Network tab (not the page's).

```typescript
// background.ts — wrapper with debugging
async function fetchWithLogging(url: string, init?: RequestInit): Promise<Response> {
  const start = performance.now();
  console.log("[NET] →", init?.method ?? "GET", url);

  try {
    const response = await fetch(url, init);
    const elapsed = (performance.now() - start).toFixed(0);
    console.log("[NET] ←", response.status, url, `(${elapsed}ms)`);

    if (!response.ok) {
      const body = await response.clone().text();
      console.error("[NET] Error body:", body.slice(0, 500));
    }
    return response;
  } catch (error) {
    console.error("[NET] FAILED", url, error);
    throw error;
  }
}
```

### From Content Scripts

Content script `fetch()` requests are subject to the **page's** CORS policy unless the URL is listed in `host_permissions`. To debug:

1. Open the web page's DevTools → Network tab
2. Filter by "Extension" origin or look for requests from `chrome-extension://...`

**Alternative:** Route requests through the service worker:

```typescript
// content-script.ts — delegate to background
const response = await chrome.runtime.sendMessage({
  type: "FETCH",
  url: "https://api.example.com/data",
});

// background.ts
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "FETCH") {
    fetch(msg.url)
      .then((r) => r.json())
      .then((data) => sendResponse({ data }))
      .catch((err) => sendResponse({ error: err.message }));
    return true; // keep port open for async response
  }
});
```

---

## Storage Inspector

### Quick Storage Dump

```typescript
// Run in any extension context's console:
chrome.storage.local.get(null, (items) => console.table(items));
chrome.storage.sync.get(null, (items) => console.table(items));
chrome.storage.session.get(null, (items) => console.table(items));
```

### Storage Change Monitoring

```typescript
// src/utils/storage-debug.ts
chrome.storage.onChanged.addListener((changes, areaName) => {
  console.group(`[STORAGE] ${areaName} changed`);
  for (const [key, { oldValue, newValue }] of Object.entries(changes)) {
    console.log(`  ${key}:`, oldValue, "→", newValue);
  }
  console.groupEnd();
});
```

### Storage Quotas

| Storage Area | Per-Item Limit | Total Limit | Persists Across Sessions |
|-------------|---------------|-------------|-------------------------|
| `storage.local` | None | 10 MB (or unlimited with `unlimitedStorage`) | Yes |
| `storage.sync` | 8,192 bytes | 102,400 bytes | Yes (synced to Google account) |
| `storage.session` | None | 10 MB | No (cleared when browser closes) |

```typescript
// Check current usage
chrome.storage.local.getBytesInUse(null, (bytes) => {
  console.log(`storage.local: ${(bytes / 1024).toFixed(1)} KB used`);
});
```

---

## Performance Profiling

### Service Worker Performance

```typescript
// Measure critical startup path
const swStart = performance.now();

// ... initialization code ...

chrome.runtime.onInstalled.addListener(() => {
  console.log(`[PERF] SW init took ${(performance.now() - swStart).toFixed(0)}ms`);
});
```

### Content Script Injection Timing

```typescript
// content-script.ts
const injectionTime = performance.now();
console.log(`[PERF] Content script parsed at ${injectionTime.toFixed(0)}ms`);

// Measure DOM manipulation
performance.mark("dom-start");
// ... DOM operations ...
performance.mark("dom-end");
performance.measure("DOM manipulation", "dom-start", "dom-end");

const measures = performance.getEntriesByType("measure");
measures.forEach((m) => console.log(`[PERF] ${m.name}: ${m.duration.toFixed(0)}ms`));
```

### Chrome Task Manager

1. Open **Chrome Menu → More Tools → Task Manager** (or Shift+Esc)
2. Find your extension in the list
3. Monitor: Memory, CPU, Network, Process ID
4. Right-click column headers to add JavaScript memory column

---

## Memory Leak Detection in Service Workers

Common causes of leaks and how to detect them:

| Leak Source | Symptom | Fix |
|-------------|---------|-----|
| Growing Map/Set/Array | Memory increases after each event | Clear collections periodically or use WeakRef |
| Event listeners not removed | Duplicate processing of events | Remove listeners in cleanup; use `AbortController` |
| Closures capturing large objects | Large retained heap | Null out references; restructure closures |
| Caching without eviction | Unbounded memory growth | Set cache size limits; use LRU eviction |

```typescript
// background.ts — bounded cache pattern
class LRUCache<K, V> {
  private map = new Map<K, V>();
  constructor(private maxSize: number) {}

  get(key: K): V | undefined {
    const value = this.map.get(key);
    if (value !== undefined) {
      // Move to end (most recently used)
      this.map.delete(key);
      this.map.set(key, value);
    }
    return value;
  }

  set(key: K, value: V): void {
    this.map.delete(key);
    this.map.set(key, value);
    if (this.map.size > this.maxSize) {
      const firstKey = this.map.keys().next().value!;
      this.map.delete(firstKey);
    }
  }
}

// Use instead of plain Map
const cache = new LRUCache<string, unknown>(100);
```

### Heap Snapshot Comparison

1. Open service worker DevTools → Memory tab
2. Take a **Heap snapshot** (baseline)
3. Perform actions that might leak (trigger events, open/close popups)
4. Take another **Heap snapshot**
5. Select "Comparison" view to see allocated/freed objects
6. Look for growing counts of detached DOM nodes, closures, or arrays

---

## Extension Reload Automation

### Using `web-ext` (works with Chrome too)

```bash
npm install -D web-ext

# Auto-reload on file change
npx web-ext run --target=chromium --source-dir=./dist --start-url="https://example.com"
```

### Manual Reload via Keyboard Shortcut

Add to `manifest.json`:

```json
{
  "commands": {
    "_reload_extension": {
      "suggested_key": { "default": "Ctrl+Shift+R", "mac": "Command+Shift+R" },
      "description": "Reload extension (dev only)"
    }
  }
}
```

```typescript
// background.ts — dev-only reload command
if (!("update_url" in chrome.runtime.getManifest())) {
  chrome.commands.onCommand.addListener((command) => {
    if (command === "_reload_extension") {
      chrome.runtime.reload();
    }
  });
}
```

### File Watcher with Auto-Reload

```typescript
// scripts/dev-reload.ts — run alongside your build watcher
import { WebSocket } from "ws";

// This server notifies the extension to reload
const wss = new WebSocket.Server({ port: 35729 });

wss.on("connection", (ws) => {
  console.log("Extension connected for live reload");
});

export function triggerReload() {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send("reload");
    }
  });
}
```

```typescript
// src/dev-client.ts — include only in dev builds
if (!("update_url" in chrome.runtime.getManifest())) {
  const ws = new WebSocket("ws://localhost:35729");
  ws.onmessage = (event) => {
    if (event.data === "reload") {
      chrome.runtime.reload();
    }
  };
  ws.onerror = () => {
    // Dev server not running — ignore silently
  };
}
```

---

## Debugging Checklist

Use this checklist when something is not working:

1. **Check `chrome://extensions`** — Is your extension loaded? Any errors shown?
2. **Check the right console** — Service worker logs are in the SW DevTools, not the page console
3. **Check permissions** — Does `manifest.json` declare the required permissions and host_permissions?
4. **Check match patterns** — Do content script `matches` cover the target URLs?
5. **Check CSP** — Is inline script/style blocked? Move to external files
6. **Check service worker state** — Is it terminated? Click "Inspect views: service worker" to wake it
7. **Check `chrome.runtime.lastError`** — Always check in callbacks
8. **Check storage** — Dump `chrome.storage.local.get(null, console.log)` to verify state
9. **Check for race conditions** — Is the service worker ready when the popup sends a message?
10. **Hard reload** — Remove and re-add the extension from `chrome://extensions`
