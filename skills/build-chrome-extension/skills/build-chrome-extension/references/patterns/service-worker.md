# Service Worker Patterns (Manifest V3)

## Lifecycle Overview

MV3 replaces persistent background pages with event-driven service workers.

```
install → activate → idle → TERMINATED (after ~30s inactivity)
                        ↑           │
                        └───────────┘  (re-launched on next event)
```

- No DOM, no `window`, no `document` — use `self` or `chrome.offscreen`.
- Terminated after **30 seconds** of inactivity. Re-launched from scratch on next event.
- All in-memory state is gone on termination.
- Listeners **must** be registered synchronously at the top level of the script.

### Manifest declaration

```jsonc
{
  "manifest_version": 3,
  "background": {
    "service_worker": "service-worker.js",
    "type": "module"   // enables ES module import statements
  }
}
```

## Top-Level Listener Registration (Critical Pattern)

Chrome only dispatches events to listeners registered **synchronously during the first
turn of the event loop**. Wrapping in `async`, `setTimeout`, or dynamic `import()` breaks it.

```typescript
// CORRECT — all listeners at top level
chrome.runtime.onInstalled.addListener((details) => handleInstall(details));
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  handleMessage(msg, sender).then(sendResponse); // async INSIDE is fine
  return true; // keeps message channel open for async response
});
chrome.alarms.onAlarm.addListener((alarm) => handleAlarm(alarm));

// WRONG — listener registered asynchronously, MISSED after restart
async function setup() {
  const config = await chrome.storage.local.get("config");
  chrome.runtime.onMessage.addListener((msg) => { /* ... */ }); // BROKEN
}
setup();
```

## The 30-Second Termination Rule

Chrome terminates the SW when these are all true for ~30s: no pending `chrome.*` event
callbacks, no active `fetch()`, no open `chrome.runtime.connect()` ports.

| Action | Keeps SW alive? |
|---|---|
| Active `chrome.runtime.Port` connection | Yes, while port is open |
| Pending `fetch()` request | Yes, until response completes |
| `chrome.alarms` handler executing | Yes, for handler duration |
| `setTimeout` / `setInterval` | **No** — does not prevent termination |
| `chrome.storage` async call in progress | Yes, until callback |
| `waitUntil()` (ExtendableEvent) | Yes (install/activate only) |

**5-minute hard limit:** Even with active work, Chrome kills the SW after 5 minutes.

## State Persistence via chrome.storage

| Property | `session` | `local` |
|---|---|---|
| Persists across SW restart | Yes | Yes |
| Persists across browser restart | **No** | Yes |
| Quota | 10 MB (1 MB default; extend with `setAccessLevel`) | 10 MB (`unlimitedStorage` for more) |
| Available in content scripts | Only with `TRUSTED_AND_UNTRUSTED_CONTEXTS` | Yes |
| Use case | Session tokens, ephemeral caches | User settings, persistent data |

```typescript
// Save/restore state that survives SW termination
await chrome.storage.session.set({ myState: { count: 42 } });
const { myState } = await chrome.storage.session.get("myState");

// Allow content scripts to access session storage
chrome.storage.session.setAccessLevel({
  accessLevel: "TRUSTED_AND_UNTRUSTED_CONTEXTS",
});

// Lazy-load pattern: in-memory cache backed by storage
let cache: Map<string, string> | null = null;
async function getCache(): Promise<Map<string, string>> {
  if (cache) return cache;
  const { data } = await chrome.storage.session.get("data");
  cache = new Map(Object.entries(data ?? {}));
  return cache;
}
```

## chrome.runtime.onInstalled

Fires on: first install, extension update, Chrome update.

```typescript
chrome.runtime.onInstalled.addListener(async (details) => {
  switch (details.reason) {
    case chrome.runtime.OnInstalledReason.INSTALL:
      await chrome.storage.local.set({ settings: { theme: "auto", sync: true } });
      chrome.tabs.create({ url: chrome.runtime.getURL("onboarding.html") });
      break;
    case chrome.runtime.OnInstalledReason.UPDATE:
      await migrateStorage(details.previousVersion!);
      break;
  }
});

async function migrateStorage(prev: string): Promise<void> {
  if (prev < "2.0.0") {
    const { oldKey } = await chrome.storage.local.get("oldKey");
    if (oldKey !== undefined) {
      await chrome.storage.local.set({ newKey: oldKey });
      await chrome.storage.local.remove("oldKey");
    }
  }
}
```

## chrome.runtime.onStartup

Fires once per browser launch (not per SW restart).

```typescript
chrome.runtime.onStartup.addListener(() => {
  chrome.storage.session.clear(); // clean stale session data
  // Ensure alarms survive browser restart
  chrome.alarms.get("periodic-sync", (alarm) => {
    if (!alarm) chrome.alarms.create("periodic-sync", { periodInMinutes: 5 });
  });
});
```

## Alarm Pulse Pattern

`chrome.alarms` is the only reliable periodic mechanism. Minimum interval: 30s (dev), 1 min (production).

```typescript
// Set up alarms at install
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("heartbeat", { periodInMinutes: 1 });
  chrome.alarms.create("data-sync", { delayInMinutes: 0.5, periodInMinutes: 5 });
});

// Handle — top-level listener
chrome.alarms.onAlarm.addListener(async (alarm) => {
  switch (alarm.name) {
    case "heartbeat": await performHealthCheck(); break;
    case "data-sync": await syncWithServer(); break;
  }
});

// One-shot delayed work
chrome.alarms.create("deferred-cleanup", { delayInMinutes: 2 });
// In handler: chrome.alarms.clear("deferred-cleanup") after execution
```

## chrome.offscreen for DOM-Dependent Tasks

Service workers have no DOM. Use offscreen documents for HTML parsing, Canvas, audio, clipboard.

```typescript
async function ensureOffscreenDocument(): Promise<void> {
  const contexts = await chrome.runtime.getContexts({
    contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
  });
  if (contexts.length > 0) return;
  await chrome.offscreen.createDocument({
    url: chrome.runtime.getURL("offscreen.html"),
    reasons: [chrome.offscreen.Reason.DOM_PARSER],
    justification: "Parse HTML content from API response",
  });
}
```

```typescript
// offscreen.ts — handles DOM work
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "parse-html") {
    const doc = new DOMParser().parseFromString(msg.html, "text/html");
    chrome.runtime.sendMessage({ type: "parse-result", data: doc.body.textContent ?? "" });
  }
});
```

| Offscreen Reason | Use case |
|---|---|
| `DOM_PARSER` | Parse HTML with DOMParser |
| `AUDIO_PLAYBACK` | Play audio |
| `CLIPBOARD` | Read/write clipboard |
| `BLOBS` | Blob URL creation |
| `DOM_SCRAPING` | querySelector on fetched HTML |
| `WORKERS` | Run a dedicated Worker |
| `LOCAL_STORAGE` | Access localStorage (migration) |

Only **one** offscreen document can exist at a time per extension.

## Keep-Alive Strategies and Tradeoffs

| Strategy | Tradeoff |
|---|---|
| `chrome.alarms` heartbeat (30s) | Minimum 30s gap; SW still dies between alarms |
| Long-lived `Port` from popup/sidepanel | Only works while that UI surface is open |
| Offscreen document holding a port | Adds complexity; offscreen doc can also be closed |
| Periodic `fetch` to slow endpoint | Wastes bandwidth; 5-min hard limit still applies |
| **Design for termination** (recommended) | Persist state, use alarms, accept restarts — most robust |

## Fetch and Network Requests

```typescript
async function fetchWithRetry(url: string, opts: RequestInit = {}, retries = 3): Promise<Response> {
  for (let i = 0; i <= retries; i++) {
    try {
      const res = await fetch(url, opts);
      if (res.ok || res.status < 500) return res;
    } catch (err) {
      if (i === retries) throw err;
    }
    await new Promise((r) => setTimeout(r, 1000 * 2 ** i));
  }
  throw new Error("Unreachable");
}
```

A pending `fetch` keeps the SW alive, but the 5-minute hard limit still applies.

## Error Handling and Crash Recovery

```typescript
// Global error handlers
self.addEventListener("error", (e) => { console.error("SW error:", e.error); });
self.addEventListener("unhandledrejection", (e) => { console.error("SW rejection:", e.reason); });

// Defensive message handler
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  handleMessage(msg, sender)
    .then(sendResponse)
    .catch((err) => sendResponse({ error: err.message }));
  return true;
});
```

### Detecting unclean shutdown

```typescript
chrome.runtime.onStartup.addListener(async () => {
  const { clean } = await chrome.storage.session.get("clean");
  if (clean === false) await recoverFromCrash();
  await chrome.storage.session.set({ clean: false });
});
// No reliable "beforeTerminate" event exists — persist state proactively.
```

## Common Service Worker Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Global mutable state (`let count = 0`) | Lost on termination | `chrome.storage.session` |
| `setInterval` for periodic work | Stops silently when SW dies | `chrome.alarms` |
| `setTimeout` for delayed tasks | SW may terminate first | `chrome.alarms` with `delayInMinutes` |
| Async top-level listener registration | Listeners missed after restart | Register synchronously at top level |
| `window.*` or `document.*` | Does not exist in SW | `self.*` or `chrome.offscreen` |
| `localStorage` / `sessionStorage` | Not available in SW | `chrome.storage.local` / `.session` |
| Not returning `true` in `onMessage` | `sendResponse` invalid before async completes | Always `return true` for async |
| Wrapping listener behind `import()` | Listener not registered on restart | Static registration; dynamic import inside handler only |
| WebSocket expecting persistence | Closes on SW termination | Reconnect on wake; queue messages in storage |
| Long computation (>5 min) | Chrome hard-kills | Break into chunks; use offscreen Worker |
| Ignoring `chrome.runtime.lastError` | Silent failures in callback APIs | Always check in callbacks |

## Complete Service Worker Template

```typescript
import { handleMessage } from "./handlers.js";

// ── ALL LISTENERS AT TOP LEVEL ──────────────────────────────────────
chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === "install") {
    await chrome.storage.local.set({ settings: { theme: "system", notify: true } });
    chrome.alarms.create("periodic-sync", { periodInMinutes: 5 });
  }
  if (details.reason === "update") await migrate(details.previousVersion!);
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.get("periodic-sync", (a) => {
    if (!a) chrome.alarms.create("periodic-sync", { periodInMinutes: 5 });
  });
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === "periodic-sync") await syncData();
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  handleMessage(msg, sender).then(sendResponse).catch((e) => sendResponse({ error: e.message }));
  return true;
});

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;
  await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content-script.js"] });
});

// ── HELPERS ──────────────────────────────────────────────────────────
async function migrate(prev: string): Promise<void> { /* version logic */ }
async function syncData(): Promise<void> {
  try {
    const data = await fetch("https://api.example.com/sync").then((r) => r.json());
    await chrome.storage.local.set({ syncedData: data });
  } catch (err) { console.error("Sync failed:", err); }
}
```
