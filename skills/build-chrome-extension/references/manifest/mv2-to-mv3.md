# MV2 to MV3 Migration — Complete Reference

## Key Differences Table

| Feature | Manifest V2 | Manifest V3 |
|---|---|---|
| Manifest version | `"manifest_version": 2` | `"manifest_version": 3` |
| Background | `"background": { "scripts": [...], "persistent": false }` | `"background": { "service_worker": "sw.js", "type": "module" }` |
| Toolbar action | `browser_action` or `page_action` | `action` (unified) |
| Network blocking | `chrome.webRequest` (blocking) | `chrome.declarativeNetRequest` (rule-based) |
| Content Security Policy | String: `"content_security_policy": "..."` | Object: `"content_security_policy": { "extension_pages": "..." }` |
| Remote code | Allowed (remote `<script>`, `eval()`) | Blocked entirely for extension pages |
| Host permissions | Inside `permissions` array | Separate `host_permissions` array |
| Web accessible resources | Flat string array | Array of objects with `matches`/`extension_ids` |
| `executeScript` | `chrome.tabs.executeScript()` | `chrome.scripting.executeScript()` |
| `insertCSS` | `chrome.tabs.insertCSS()` | `chrome.scripting.insertCSS()` |
| Promises | Callbacks only | Promises (callbacks still supported) |
| Service worker lifetime | Persistent (optional) | Ephemeral (max ~30s idle, 5m active) |

---

## Background Pages to Service Workers

### What Changes

| MV2 Background Page | MV3 Service Worker |
|---|---|
| Has DOM access (`document`, `window`) | No DOM access |
| Can use `XMLHttpRequest` | Must use `fetch()` |
| Can run persistently | Terminates after ~30s of inactivity |
| Can use `localStorage` | Must use `chrome.storage` |
| Multiple script files | Single entry point (use `import` with `"type": "module"`) |
| `chrome.extension.getBackgroundPage()` | Not available — use message passing |

### MV2 Background Page

```jsonc
// MV2 manifest.json
{
  "background": {
    "scripts": ["bg-utils.js", "bg-main.js"],
    "persistent": false
  }
}
```

```typescript
// MV2 — bg-main.js (event page)
let counter = 0; // persists while page is alive

chrome.browserAction.onClicked.addListener((tab) => {
  counter++;
  const xhr = new XMLHttpRequest();
  xhr.open("GET", "https://api.example.com/data");
  xhr.onload = () => {
    localStorage.setItem("lastResult", xhr.responseText);
  };
  xhr.send();
});
```

### MV3 Service Worker

```jsonc
// MV3 manifest.json
{
  "background": {
    "service_worker": "background.js",
    "type": "module"
  }
}
```

```typescript
// MV3 — background.ts (service worker)
import { processData } from "./lib/utils.js";

// State does NOT persist — use chrome.storage.session for ephemeral state
chrome.runtime.onInstalled.addListener(async () => {
  await chrome.storage.session.set({ counter: 0 });
});

chrome.action.onClicked.addListener(async (tab) => {
  const { counter } = await chrome.storage.session.get("counter");
  await chrome.storage.session.set({ counter: counter + 1 });

  const response = await fetch("https://api.example.com/data");
  const data = await response.text();
  await chrome.storage.local.set({ lastResult: data });
});
```

### Handling Service Worker Termination

The service worker can terminate at any time. Common patterns to handle this:

```typescript
// PROBLEM: Global variables reset on restart
let cache: Map<string, string> = new Map(); // lost on termination

// SOLUTION: Use chrome.storage.session (in-memory, survives restarts within session)
async function getCache(key: string): Promise<string | undefined> {
  const result = await chrome.storage.session.get(key);
  return result[key];
}

async function setCache(key: string, value: string): Promise<void> {
  await chrome.storage.session.set({ [key]: value });
}
```

```typescript
// PROBLEM: setInterval / setTimeout don't survive termination
setInterval(() => pollServer(), 60_000); // will NOT fire after termination

// SOLUTION: Use chrome.alarms
chrome.alarms.create("poll-server", { periodInMinutes: 1 });

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === "poll-server") {
    await pollServer();
  }
});
```

```typescript
// PROBLEM: Accessing window/document objects
const div = document.createElement("div"); // ERROR: document is not defined

// SOLUTION: Use offscreen documents when DOM access is needed
async function parseHTML(html: string): Promise<string> {
  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: [chrome.offscreen.Reason.DOM_PARSER],
    justification: "Parse HTML content",
  });

  const result = await chrome.runtime.sendMessage({
    action: "parseHTML",
    html,
  });

  await chrome.offscreen.closeDocument();
  return result;
}
```

### Keeping the Service Worker Alive (When Necessary)

```typescript
// For long-running operations, use a keep-alive pattern
// (only when genuinely needed — avoid for normal operations)
async function keepAlive(promise: Promise<unknown>): Promise<void> {
  const keepAliveInterval = setInterval(() => {
    chrome.runtime.getPlatformInfo(() => {
      // no-op, just keeps SW alive
    });
  }, 25_000);

  try {
    await promise;
  } finally {
    clearInterval(keepAliveInterval);
  }
}
```

---

## webRequest to declarativeNetRequest

### MV2: webRequest (Blocking)

```jsonc
// MV2 manifest.json
{
  "permissions": [
    "webRequest",
    "webRequestBlocking",
    "*://*.example.com/*"
  ]
}
```

```typescript
// MV2 — blocking requests dynamically
chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (details.url.includes("tracker")) {
      return { cancel: true };
    }
    if (details.url.includes("old-api")) {
      return { redirectUrl: details.url.replace("old-api", "new-api") };
    }
    return {};
  },
  { urls: ["*://*.example.com/*"] },
  ["blocking"]
);

// MV2 — modifying headers
chrome.webRequest.onBeforeSendHeaders.addListener(
  (details) => {
    details.requestHeaders?.push({
      name: "X-Custom-Header",
      value: "my-extension",
    });
    return { requestHeaders: details.requestHeaders };
  },
  { urls: ["*://*.example.com/*"] },
  ["blocking", "requestHeaders"]
);
```

### MV3: declarativeNetRequest (Rule-Based)

```jsonc
// MV3 manifest.json
{
  "permissions": ["declarativeNetRequest"],
  "host_permissions": ["*://*.example.com/*"],
  "declarative_net_request": {
    "rule_resources": [{
      "id": "my_rules",
      "enabled": true,
      "path": "rules.json"
    }]
  }
}
```

```jsonc
// rules.json — static rules
[
  {
    "id": 1,
    "priority": 1,
    "action": { "type": "block" },
    "condition": {
      "urlFilter": "tracker",
      "domains": ["example.com"],
      "resourceTypes": ["script", "xmlhttprequest", "image"]
    }
  },
  {
    "id": 2,
    "priority": 1,
    "action": {
      "type": "redirect",
      "redirect": {
        "transform": {
          "host": "new-api.example.com"
        }
      }
    },
    "condition": {
      "urlFilter": "||old-api.example.com",
      "resourceTypes": ["xmlhttprequest"]
    }
  },
  {
    "id": 3,
    "priority": 1,
    "action": {
      "type": "modifyHeaders",
      "requestHeaders": [
        {
          "header": "X-Custom-Header",
          "operation": "set",
          "value": "my-extension"
        }
      ]
    },
    "condition": {
      "urlFilter": "||example.com",
      "resourceTypes": ["xmlhttprequest"]
    }
  }
]
```

```typescript
// MV3 — dynamic rules (added at runtime)
await chrome.declarativeNetRequest.updateDynamicRules({
  removeRuleIds: [100],
  addRules: [
    {
      id: 100,
      priority: 1,
      action: { type: chrome.declarativeNetRequest.RuleActionType.BLOCK },
      condition: {
        urlFilter: "||ads.newsite.com",
        resourceTypes: [
          chrome.declarativeNetRequest.ResourceType.SCRIPT,
        ],
      },
    },
  ],
});
```

### webRequest Migration Decision Tree

```
MV2 webRequest usage:
  Blocking requests? → declarativeNetRequest rules (block action)
  Redirecting? → declarativeNetRequest rules (redirect action)
  Modifying headers? → declarativeNetRequest rules (modifyHeaders action)
  Observing only (no modification)? → webRequest still works in MV3 (read-only)
  Complex dynamic logic (needs JS)? → Use dynamic rules + chrome.declarativeNetRequest.updateDynamicRules()
  Content-based decisions? → Not directly possible; use content scripts + messaging
```

### What webRequest Can Still Do in MV3

`webRequest` is NOT removed in MV3 — only blocking capabilities are removed. You can still:
- Observe requests (onBeforeRequest, onCompleted, onErrorOccurred)
- Read headers (without modifying)
- Debug and log network activity

```typescript
// MV3 — webRequest for observation (non-blocking)
chrome.webRequest.onCompleted.addListener(
  (details) => {
    console.log(`Request completed: ${details.url} (${details.statusCode})`);
  },
  { urls: ["*://*.example.com/*"] }
);
```

---

## Content Security Policy Changes

### MV2 CSP

```jsonc
// MV2 — single string, could allow remote scripts
{
  "content_security_policy": "script-src 'self' https://cdn.example.com; object-src 'self'"
}
```

### MV3 CSP

```jsonc
// MV3 — object format, no remote scripts allowed
{
  "content_security_policy": {
    "extension_pages": "script-src 'self' 'wasm-unsafe-eval'; object-src 'self'",
    "sandbox": "sandbox allow-scripts; script-src 'self' https://cdn.example.com"
  }
}
```

| What | MV2 | MV3 |
|---|---|---|
| Remote `<script src>` | Allowed with CSP declaration | Blocked — bundle all code |
| `eval()` / `new Function()` | Allowed with `'unsafe-eval'` in CSP | Blocked entirely on extension pages |
| `'wasm-unsafe-eval'` | N/A | Allowed — enables WebAssembly |
| Inline scripts | Allowed with `'unsafe-inline'` or nonces | Blocked for scripts, allowed for styles |
| Sandbox pages | Same string format | Separate `sandbox` key, can load remote scripts |

---

## Remote Code Execution Removal

### What's Blocked in MV3

```typescript
// ALL of these are BLOCKED in MV3 extension pages:

eval("console.log('blocked')");

new Function("return 1 + 1")();

const script = document.createElement("script");
script.src = "https://cdn.example.com/lib.js"; // blocked
document.head.appendChild(script);

// Dynamically imported remote modules
import("https://cdn.example.com/module.js"); // blocked
```

### Migration Strategies

```typescript
// STRATEGY 1: Bundle all dependencies
// Instead of loading from CDN at runtime, bundle with your build tool
// package.json: "build": "esbuild src/background.ts --bundle --outfile=dist/background.js"

// STRATEGY 2: Use sandbox pages for unavoidable remote code
// Create a sandboxed iframe that CAN load remote scripts
// but has no Chrome API access

// manifest.json
// "sandbox": { "pages": ["sandbox.html"] }

// sandbox.html
// <script src="https://cdn.example.com/lib.js"></script>
// <script src="sandbox-bridge.js"></script>

// Communicate via postMessage
// In extension page:
const iframe = document.createElement("iframe");
iframe.src = chrome.runtime.getURL("sandbox.html");
iframe.style.display = "none";
document.body.appendChild(iframe);

iframe.contentWindow!.postMessage({ action: "compute", data: input }, "*");

window.addEventListener("message", (event) => {
  if (event.source === iframe.contentWindow) {
    console.log("Result from sandbox:", event.data);
  }
});

// STRATEGY 3: Use chrome.scripting for dynamic content scripts
// Instead of eval in content scripts, inject functions directly
await chrome.scripting.executeScript({
  target: { tabId },
  func: (param: string) => {
    // This function is serialized and injected — not eval'd
    document.title = param;
  },
  args: ["New Title"],
});
```

---

## Action API Changes

### MV2: Separate APIs

```jsonc
// MV2 — browser_action (always visible)
{
  "browser_action": {
    "default_icon": "icon.png",
    "default_popup": "popup.html",
    "default_title": "My Extension"
  }
}

// MV2 — page_action (conditionally visible)
{
  "page_action": {
    "default_icon": "icon.png",
    "default_popup": "popup.html"
  }
}
```

```typescript
// MV2 API calls
chrome.browserAction.setIcon({ path: "icon-active.png" });
chrome.browserAction.setBadgeText({ text: "3" });
chrome.pageAction.show(tabId);
chrome.pageAction.hide(tabId);
```

### MV3: Unified `action`

```jsonc
// MV3 — single action API
{
  "action": {
    "default_icon": {
      "16": "icons/icon-16.png",
      "32": "icons/icon-32.png"
    },
    "default_popup": "popup.html",
    "default_title": "My Extension"
  }
}
```

```typescript
// MV3 API calls
chrome.action.setIcon({ path: "icon-active.png" });
chrome.action.setBadgeText({ text: "3" });
chrome.action.setBadgeBackgroundColor({ color: "#FF0000" });
chrome.action.setBadgeTextColor({ color: "#FFFFFF" });

// MV3 equivalent of page_action show/hide:
chrome.action.enable(tabId);   // replaces pageAction.show()
chrome.action.disable(tabId);  // replaces pageAction.hide()

// Conditionally show on specific pages using declarativeContent
chrome.runtime.onInstalled.addListener(() => {
  chrome.action.disable(); // disable globally by default

  chrome.declarativeContent.onPageChanged.removeRules(undefined, () => {
    chrome.declarativeContent.onPageChanged.addRules([
      {
        conditions: [
          new chrome.declarativeContent.PageStateMatcher({
            pageUrl: { hostEquals: "example.com" },
          }),
        ],
        actions: [new chrome.declarativeContent.ShowAction()],
      },
    ]);
  });
});
```

### API Name Mapping

| MV2 | MV3 |
|---|---|
| `chrome.browserAction.*` | `chrome.action.*` |
| `chrome.pageAction.*` | `chrome.action.*` (with `enable`/`disable`) |
| `chrome.browserAction.onClicked` | `chrome.action.onClicked` |
| `chrome.pageAction.onClicked` | `chrome.action.onClicked` |
| `chrome.pageAction.show(tabId)` | `chrome.action.enable(tabId)` |
| `chrome.pageAction.hide(tabId)` | `chrome.action.disable(tabId)` |

---

## Script Injection Changes

### MV2

```typescript
// MV2 — chrome.tabs.executeScript
chrome.tabs.executeScript(tabId, {
  file: "content.js",
  allFrames: true,
  runAt: "document_idle",
});

chrome.tabs.executeScript(tabId, {
  code: 'document.title = "Hello"',  // arbitrary code string — blocked in MV3
});

chrome.tabs.insertCSS(tabId, {
  file: "styles.css",
});
```

### MV3

```typescript
// MV3 — chrome.scripting.executeScript
// Requires "scripting" permission
await chrome.scripting.executeScript({
  target: { tabId, allFrames: true },
  files: ["content.js"],
});

// Inject a function (not a code string)
await chrome.scripting.executeScript({
  target: { tabId },
  func: (greeting: string) => {
    document.title = greeting;
    return document.title;
  },
  args: ["Hello"],
  world: "ISOLATED",
});

await chrome.scripting.insertCSS({
  target: { tabId },
  files: ["styles.css"],
});

// Register content scripts dynamically
await chrome.scripting.registerContentScripts([
  {
    id: "dynamic-script",
    matches: ["https://example.com/*"],
    js: ["dynamic-content.js"],
    runAt: "document_idle",
    persistAcrossSessions: true,
  },
]);

// Unregister
await chrome.scripting.unregisterContentScripts({
  ids: ["dynamic-script"],
});
```

---

## Promise Support

### MV2: Callbacks Only

```typescript
// MV2 — callbacks
chrome.tabs.query({ active: true }, (tabs) => {
  chrome.tabs.sendMessage(tabs[0].id!, { action: "getData" }, (response) => {
    chrome.storage.local.set({ data: response }, () => {
      console.log("Saved");
    });
  });
});
```

### MV3: Promises (Callbacks Still Work)

```typescript
// MV3 — async/await
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
const response = await chrome.tabs.sendMessage(tab.id!, { action: "getData" });
await chrome.storage.local.set({ data: response });
console.log("Saved");
```

---

## Step-by-Step Migration Checklist

### Phase 1: Manifest Changes

- [ ] Change `"manifest_version": 2` to `"manifest_version": 3`
- [ ] Replace `"background": { "scripts": [...] }` with `"background": { "service_worker": "background.js", "type": "module" }`
- [ ] Replace `"browser_action"` or `"page_action"` with `"action"`
- [ ] Move host permissions from `"permissions"` to `"host_permissions"`
- [ ] Convert `"content_security_policy"` from string to object format
- [ ] Convert `"web_accessible_resources"` from flat array to array of objects with `matches`

### Phase 2: Background Script Migration

- [ ] Merge all background scripts into a single entry point using ES module imports
- [ ] Remove all DOM access (`document.*`, `window.*` except `self`)
- [ ] Replace `XMLHttpRequest` with `fetch()`
- [ ] Replace `localStorage` with `chrome.storage.local` or `chrome.storage.session`
- [ ] Replace `setTimeout`/`setInterval` for long-period timers with `chrome.alarms`
- [ ] Add state persistence — global variables reset when service worker terminates
- [ ] Handle service worker startup — re-register event listeners at top level (not inside callbacks)

### Phase 3: API Migration

- [ ] Replace `chrome.browserAction.*` with `chrome.action.*`
- [ ] Replace `chrome.pageAction.*` with `chrome.action.*` + `enable()`/`disable()`
- [ ] Replace `chrome.tabs.executeScript()` with `chrome.scripting.executeScript()`
- [ ] Replace `chrome.tabs.insertCSS()` with `chrome.scripting.insertCSS()`
- [ ] Add `"scripting"` to permissions if using `chrome.scripting`
- [ ] Replace `chrome.extension.getBackgroundPage()` with message passing
- [ ] Convert callbacks to promises/async-await (optional but recommended)

### Phase 4: Network Request Migration

- [ ] Identify all `webRequest` blocking listeners
- [ ] Create `declarativeNetRequest` rule files for blocking/redirecting
- [ ] Add `"declarativeNetRequest"` to permissions
- [ ] Convert dynamic blocking logic to dynamic rules (`updateDynamicRules`)
- [ ] Keep read-only `webRequest` listeners as-is (they still work)
- [ ] Remove `"webRequestBlocking"` from permissions

### Phase 5: Code Execution Changes

- [ ] Remove all `eval()` and `new Function()` calls
- [ ] Bundle all third-party libraries (no remote script loading)
- [ ] Replace `chrome.tabs.executeScript({ code: "..." })` with `chrome.scripting.executeScript({ func: ... })`
- [ ] Move any code that requires `eval()` to a sandboxed page

### Phase 6: Testing

- [ ] Test service worker lifecycle (idle termination, wake-up on events)
- [ ] Test all content scripts on target pages
- [ ] Verify `declarativeNetRequest` rules fire correctly
- [ ] Test in incognito mode
- [ ] Test after browser restart
- [ ] Verify alarms fire at expected intervals
- [ ] Test `chrome.storage.session` state persistence across service worker restarts

---

## Common Migration Pitfalls

### Pitfall 1: Event Listeners Inside Async Calls

```typescript
// BROKEN: Listener registered inside async callback — missed on restart
chrome.storage.local.get("config", (config) => {
  chrome.action.onClicked.addListener(() => {
    // This listener is lost when the service worker restarts
  });
});

// CORRECT: Register at top level, unconditionally
chrome.action.onClicked.addListener(async () => {
  const { config } = await chrome.storage.local.get("config");
  // use config
});
```

### Pitfall 2: Assuming the Service Worker Stays Alive

```typescript
// BROKEN: WebSocket connection in service worker
const ws = new WebSocket("wss://example.com");
ws.onmessage = (event) => { /* ... */ }; // dies in ~30 seconds

// CORRECT: Use push notifications or polling with alarms
chrome.alarms.create("check-updates", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === "check-updates") {
    const response = await fetch("https://api.example.com/updates");
    const data = await response.json();
    if (data.hasUpdates) {
      chrome.notifications.create({ /* ... */ });
    }
  }
});
```

### Pitfall 3: Using window or document in Service Worker

```typescript
// BROKEN: No DOM in service workers
const parser = new DOMParser();
const doc = parser.parseFromString(html, "text/html");

// CORRECT: Use an offscreen document
// manifest.json: "permissions": ["offscreen"]
await chrome.offscreen.createDocument({
  url: "offscreen.html",
  reasons: [chrome.offscreen.Reason.DOM_PARSER],
  justification: "Parse HTML response",
});
// Send HTML to offscreen document via messaging, parse there, return result
```

### Pitfall 4: Forgetting to Handle the `type: "module"` Requirement

```typescript
// BROKEN: Using require() or importScripts() in module service worker
importScripts("lib.js"); // fails with type: "module"

// CORRECT: Use ES imports
import { helper } from "./lib.js";
```

Note: when `"type": "module"` is set, `importScripts()` is not available. Without `"type": "module"`, `import`/`export` syntax is not available. Choose one approach and be consistent.

### Pitfall 5: Blocking webRequest Migration Incomplete

```typescript
// BROKEN: Still using blocking webRequest (MV3 ignores "blocking")
chrome.webRequest.onBeforeRequest.addListener(
  (details) => ({ cancel: true }),
  { urls: ["*://*.ads.example.com/*"] },
  ["blocking"] // "blocking" is silently ignored in MV3 — request proceeds
);

// CORRECT: Use declarativeNetRequest
// (see declarativeNetRequest section above)
```

### Pitfall 6: Not Bundling Extension Code

MV3 service workers require a single entry point. If you have multiple background scripts:

```typescript
// MV2 — multiple scripts loaded in order
// "background": { "scripts": ["a.js", "b.js", "c.js"] }

// MV3 — single entry, import the rest
// background.ts
import "./a.js";
import "./b.js";
import "./c.js";

// Or better — use a bundler (esbuild, webpack, rollup)
// esbuild src/background/index.ts --bundle --outfile=dist/background.js --format=esm
```

### Pitfall 7: Host Permissions Not Separated

```jsonc
// MV2 — host patterns mixed with permissions
{
  "permissions": [
    "storage",
    "tabs",
    "https://*.example.com/*",
    "*://api.service.com/*"
  ]
}

// MV3 — must separate
{
  "permissions": ["storage", "tabs"],
  "host_permissions": [
    "https://*.example.com/*",
    "*://api.service.com/*"
  ]
}
```

If host patterns remain in `permissions`, Chrome will reject the manifest with an error.

### Pitfall 8: Assuming Synchronous `getBackgroundPage()`

```typescript
// MV2 — direct access to background page
const bg = chrome.extension.getBackgroundPage();
bg.someGlobalFunction();

// MV3 — use message passing
// In popup/options:
const result = await chrome.runtime.sendMessage({ action: "someFunction" });

// In service worker:
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "someFunction") {
    sendResponse(someGlobalFunction());
    return true; // keep channel open for async response
  }
});
```
