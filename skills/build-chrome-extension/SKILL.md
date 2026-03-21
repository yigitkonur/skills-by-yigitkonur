---
name: build-chrome-extension
description: Use skill if you are building or debugging a Chrome extension with Manifest V3 — service workers, content scripts, popup/sidepanel, messaging, storage, permissions, testing, or Web Store publishing.
---

# Build Chrome Extension

Build production-grade Chrome extensions with Manifest V3.

## Trigger boundary

Use this skill when the task involves:

- Creating a new Chrome or browser extension from scratch
- Adding features to an existing extension (content scripts, popups, sidepanels, background logic)
- Debugging extension-specific issues (service worker termination, messaging failures, permission errors)
- Migrating from Manifest V2 to V3
- Packaging and publishing to Chrome Web Store
- Choosing between extension frameworks (WXT, Plasmo, CRXJS, vanilla)

Do NOT use this skill for:

- General web development without extension context
- Browser automation or testing (use run-agent-browser or similar)
- Chrome DevTools Protocol / CDP debugging of websites
- PWA / service worker development outside extensions
- React/Vue/Angular component development (use frontend-design)

## The Persistence Paradox — read this first

Service workers in MV3 extensions terminate after 30 seconds of inactivity. This is the #1 source of bugs in AI-generated extensions.

**Rules:**
- NEVER store state in global variables — use `chrome.storage.local` or `chrome.storage.session`
- NEVER rely on `setTimeout`/`setInterval` for long-running tasks — use `chrome.alarms`
- ALWAYS register event listeners at the top level (not inside async callbacks)
- Use `chrome.offscreen` for tasks requiring DOM access from background

```typescript
// WRONG — state lost on SW termination
let count = 0;
chrome.action.onClicked.addListener(() => { count++; });

// RIGHT — persisted across restarts
chrome.action.onClicked.addListener(async () => {
  const { count = 0 } = await chrome.storage.local.get('count');
  await chrome.storage.local.set({ count: count + 1 });
});
```

## Decision tree

```
User request
├─ "Create / scaffold a new extension"
│   → Read references/manifest/manifest-v3.md
│   → Read references/frameworks/comparison.md
│   → Follow: New Extension Workflow (below)
│
├─ "Add feature to existing extension"
│   ├─ Content script work → Read references/patterns/content-scripts.md
│   ├─ Background / service worker → Read references/patterns/service-worker.md
│   ├─ UI (popup/options/sidepanel) → Read references/patterns/ui-surfaces.md
│   ├─ Messaging between contexts → Read references/apis/messaging.md
│   ├─ Storage / state management → Read references/apis/storage.md
│   └─ Permissions → Read references/manifest/permissions.md
│
├─ "Debug an extension issue"
│   ├─ Service worker dies/restarts → Read references/patterns/service-worker.md
│   ├─ Content script not injecting → Read references/patterns/content-scripts.md
│   ├─ Messaging failures → Read references/apis/messaging.md
│   ├─ Permission errors → Read references/manifest/permissions.md
│   └─ General → Read references/testing/debugging.md
│
├─ "Test the extension"
│   → Read references/testing/testing-guide.md
│
├─ "Publish to Chrome Web Store"
│   → Read references/publishing/web-store.md
│
└─ "Migrate MV2 → MV3"
    → Read references/manifest/mv2-to-mv3.md
```

## New Extension Workflow

### Phase 1: Requirements

1. Identify the extension type: popup-only, content-script-driven, background-heavy, or full-featured
2. List required Chrome APIs (storage, tabs, scripting, declarativeNetRequest, sidePanel, etc.)
3. Determine minimum permissions using the principle of least privilege
4. Choose a framework or vanilla approach (read `references/frameworks/comparison.md`)

### Phase 2: Scaffold

Generate the project structure:

```
my-extension/
├── manifest.json              # Extension manifest (V3)
├── src/
│   ├── background/
│   │   └── service-worker.ts  # Background service worker
│   ├── content/
│   │   └── content-script.ts  # Content scripts (if needed)
│   ├── popup/
│   │   ├── popup.html
│   │   ├── popup.ts
│   │   └── popup.css
│   ├── options/               # Options page (if needed)
│   ├── sidepanel/             # Side panel (if needed)
│   └── lib/
│       ├── messaging.ts       # Type-safe message passing
│       └── storage.ts         # Type-safe storage helpers
├── icons/
│   ├── icon-16.png
│   ├── icon-48.png
│   └── icon-128.png
├── _locales/                  # i18n (if needed)
│   └── en/
│       └── messages.json
├── tsconfig.json
├── package.json
└── vite.config.ts             # Or framework config
```

### Phase 3: Implement

Build each component following the patterns in the reference files. Key principles:

- **Service worker**: Stateless, event-driven, all listeners registered at top level
- **Content scripts**: Idempotent, isolated world by default, use MAIN world only when needed
- **Messaging**: Type-safe with defined message types, always handle errors
- **Storage**: Prefer `chrome.storage.session` for ephemeral data, `local` for persistent
- **Permissions**: Request optional permissions at runtime when possible

### Phase 4: Test

Read `references/testing/testing-guide.md` for the full testing approach:

- Unit test business logic with Vitest
- Integration test Chrome APIs with Puppeteer or Playwright
- Manual load in `chrome://extensions` with Developer Mode
- Test service worker restart resilience

### Phase 5: Package and Publish

Read `references/publishing/web-store.md` for store submission:

- Prepare store assets (screenshots 1280x800, promo images, descriptions)
- Review permission justifications
- Build production bundle and create `.zip`
- Submit via Chrome Web Store Developer Dashboard

## Manifest V3 — minimal valid manifest

```json
{
  "manifest_version": 3,
  "name": "My Extension",
  "version": "1.0.0",
  "description": "A brief description of the extension.",
  "permissions": [],
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon-16.png",
      "48": "icons/icon-48.png",
      "128": "icons/icon-128.png"
    }
  },
  "icons": {
    "16": "icons/icon-16.png",
    "48": "icons/icon-48.png",
    "128": "icons/icon-128.png"
  }
}
```

Add fields as needed:

| Feature | Manifest field |
|---------|---------------|
| Background logic | `"background": { "service_worker": "background.js", "type": "module" }` |
| Content scripts | `"content_scripts": [{ "matches": [...], "js": [...] }]` |
| Options page | `"options_page": "options.html"` or `"options_ui": { "page": "options.html", "open_in_tab": false }` |
| Side panel | `"side_panel": { "default_path": "sidepanel.html" }` |
| Context menus | Add `"contextMenus"` to permissions |
| Keyboard shortcuts | `"commands": { ... }` |
| Network rules | `"declarative_net_request": { "rule_resources": [...] }` |

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Global variables lost after SW terminates | Use `chrome.storage.local` / `chrome.storage.session` |
| Event listeners not firing after restart | Register listeners at the top level of SW, never inside async |
| Content script not injecting | Check `matches` patterns, verify `host_permissions`, check page CSP |
| `chrome.tabs.sendMessage` fails | Content script must be loaded first; use `chrome.scripting.executeScript` as fallback |
| CORS errors from extension | Use `host_permissions` for the target domain |
| `eval()` blocked by CSP | MV3 forbids `eval`; use `chrome.scripting.executeScript` with `world: 'MAIN'` |
| Storage sync quota exceeded | `chrome.storage.sync` has 100KB total limit; use `local` for large data |
| Extension not reloading changes | Use `chrome.runtime.reload()` or enable auto-reload via framework |
| Side panel not showing | Requires Chrome 114+; add `"sidePanel"` permission |
| `chrome.scripting` undefined | Add `"scripting"` permission to manifest |

## Type-safe messaging pattern

```typescript
// shared/messages.ts — define once, import everywhere
type MessageMap = {
  'GET_TAB_DATA': { tabId: number };
  'TAB_DATA_RESULT': { title: string; url: string };
  'TOGGLE_FEATURE': { enabled: boolean };
};

type MessageType = keyof MessageMap;

interface TypedMessage<T extends MessageType> {
  type: T;
  payload: MessageMap[T];
}

function sendMessage<T extends MessageType>(
  msg: TypedMessage<T>
): Promise<any> {
  return chrome.runtime.sendMessage(msg);
}

function onMessage<T extends MessageType>(
  type: T,
  handler: (payload: MessageMap[T], sender: chrome.runtime.MessageSender) => void | Promise<any>
) {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === type) {
      const result = handler(message.payload, sender);
      if (result instanceof Promise) {
        result.then(sendResponse);
        return true; // Keep channel open for async response
      }
    }
  });
}
```

## Type-safe storage pattern

```typescript
// shared/storage.ts
interface StorageSchema {
  settings: { theme: 'light' | 'dark'; notifications: boolean };
  cache: { lastSync: number; data: unknown[] };
  count: number;
}

async function getStorage<K extends keyof StorageSchema>(
  key: K
): Promise<StorageSchema[K] | undefined> {
  const result = await chrome.storage.local.get(key);
  return result[key];
}

async function setStorage<K extends keyof StorageSchema>(
  key: K, value: StorageSchema[K]
): Promise<void> {
  await chrome.storage.local.set({ [key]: value });
}

function watchStorage<K extends keyof StorageSchema>(
  key: K,
  callback: (newValue: StorageSchema[K], oldValue: StorageSchema[K]) => void
): void {
  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === 'local' && key in changes) {
      callback(changes[key].newValue, changes[key].oldValue);
    }
  });
}
```

## Red flags — stop and fix immediately

| Red flag | Why it's dangerous |
|----------|--------------------|
| Global `let`/`var` in service worker | Lost on every SW restart (every 30s idle) |
| `setInterval` in service worker | Cleared on termination; use `chrome.alarms` |
| Missing `return true` in async message handler | Response channel closes before async completes |
| `"permissions": ["<all_urls>"]` | Over-broad; triggers Web Store review flags |
| Inline scripts in HTML | Blocked by MV3 CSP; use separate `.js` files |
| `document` access in service worker | No DOM in SW; use `chrome.offscreen` if DOM needed |
| `XMLHttpRequest` in service worker | Use `fetch()` instead; XHR unavailable in SW |
| Content script assumes DOM is ready | Use `"run_at": "document_idle"` or wait for elements |

## Reference routing

### Manifest and permissions

| File | Read when |
|------|-----------|
| `references/manifest/manifest-v3.md` | Setting up or modifying manifest.json, understanding required vs optional fields |
| `references/manifest/permissions.md` | Choosing permissions, understanding risk levels, requesting optional permissions |
| `references/manifest/mv2-to-mv3.md` | Migrating an existing MV2 extension to MV3 |

### Chrome APIs

| File | Read when |
|------|-----------|
| `references/apis/messaging.md` | Implementing communication between popup, content script, service worker, or external pages |
| `references/apis/storage.md` | Using chrome.storage (local, sync, session), understanding quotas and watching changes |
| `references/apis/core-apis.md` | Using tabs, scripting, alarms, notifications, contextMenus, commands, declarativeNetRequest, sidePanel, offscreen |

### Extension patterns

| File | Read when |
|------|-----------|
| `references/patterns/service-worker.md` | Writing background service workers, handling lifecycle, persistence, alarms, offscreen |
| `references/patterns/content-scripts.md` | Injecting into web pages, MAIN vs ISOLATED world, dynamic injection, shadow DOM isolation |
| `references/patterns/ui-surfaces.md` | Building popup, options page, side panel, or DevTools panel UI |

### Frameworks

| File | Read when |
|------|-----------|
| `references/frameworks/comparison.md` | Choosing between WXT, Plasmo, CRXJS Vite, or vanilla; framework setup guides |

### Testing and publishing

| File | Read when |
|------|-----------|
| `references/testing/testing-guide.md` | Unit testing, integration testing, manual testing, CI/CD for extensions |
| `references/testing/debugging.md` | Debugging service worker issues, content script problems, messaging failures |
| `references/publishing/web-store.md` | Chrome Web Store submission, asset requirements, review process, update workflow |

## Guardrails

- NEVER generate Manifest V2 extensions. Always use `"manifest_version": 3`.
- NEVER use `eval()`, `new Function()`, or inline scripts in MV3 extensions.
- NEVER store secrets (API keys, tokens) in extension code or storage without encryption.
- NEVER use `"permissions": ["<all_urls>"]` without explicit justification.
- NEVER use global variables for state in service workers.
- ALWAYS register service worker event listeners synchronously at the top level.
- ALWAYS handle the case where content scripts haven't loaded yet when sending messages.
- ALWAYS use TypeScript for extensions with more than one file.
- ALWAYS validate data at boundaries (messages received, storage reads, external API responses).
- PREFER `chrome.storage.session` over `chrome.storage.local` for ephemeral data.
- PREFER optional permissions requested at runtime over declared permissions.
- PREFER `declarativeNetRequest` over `webRequest` for network modification.
