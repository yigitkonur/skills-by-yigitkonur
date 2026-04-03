# Core Chrome Extension APIs Reference

Quick-reference for the most-used Manifest V3 APIs. Each section covers key methods, a practical code snippet, required permissions, and when to reach for the API.

---

## chrome.tabs

**Permission:** None for basic query/create. `"tabs"` permission only needed to read `url`, `title`, `favIconUrl` fields.

**Key methods:** `query`, `create`, `update`, `remove`, `get`, `onUpdated`, `onActivated`, `onRemoved`

```typescript
// Query the active tab in the current window
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
console.log(tab.id, tab.url); // url requires "tabs" permission

// Open a new tab
const newTab = await chrome.tabs.create({
  url: "https://example.com",
  active: false, // open in background
});

// Update current tab's URL
await chrome.tabs.update(tab.id!, { url: "https://example.com/new-page" });

// Close tabs
await chrome.tabs.remove([tab.id!, newTab.id!]);

// Listen for navigation completion
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url?.includes("example.com")) {
    console.log(`Tab ${tabId} finished loading`);
  }
});

// Track active tab changes
chrome.tabs.onActivated.addListener(({ tabId, windowId }) => {
  console.log(`Switched to tab ${tabId} in window ${windowId}`);
});
```

**When to use:** Tab management, opening extension pages, injecting scripts conditionally, tracking user navigation for context-aware features.

---

## chrome.scripting

**Permission:** `"scripting"` (plus host permissions for the target URLs)

**Replaces:** The deprecated `chrome.tabs.executeScript` and `chrome.tabs.insertCSS` from MV2.

**Key methods:** `executeScript`, `insertCSS`, `removeCSS`, `registerContentScripts`, `unregisterContentScripts`, `getRegisteredContentScripts`

```typescript
// Execute a function in a tab
const results = await chrome.scripting.executeScript({
  target: { tabId: tab.id! },
  func: (greeting: string) => {
    document.title = greeting;
    return document.title;
  },
  args: ["Hello from extension"],
});
console.log(results[0].result); // "Hello from extension"

// Execute a file
await chrome.scripting.executeScript({
  target: { tabId: tab.id!, allFrames: true }, // inject in all frames
  files: ["scripts/injected.js"],
});

// Execute in the MAIN world (page context, not isolated)
await chrome.scripting.executeScript({
  target: { tabId: tab.id! },
  func: () => {
    // Can access page's JS variables here
    console.log((window as any).APP_CONFIG);
  },
  world: "MAIN",
});

// Insert CSS
await chrome.scripting.insertCSS({
  target: { tabId: tab.id! },
  css: "body { border: 3px solid red !important; }",
});

// Remove previously inserted CSS
await chrome.scripting.removeCSS({
  target: { tabId: tab.id! },
  css: "body { border: 3px solid red !important; }",
});

// Dynamically register a content script (persists across restarts)
await chrome.scripting.registerContentScripts([
  {
    id: "dynamic-helper",
    matches: ["https://example.com/*"],
    js: ["scripts/helper.js"],
    runAt: "document_idle",
    persistAcrossSessions: true,
  },
]);
```

**When to use:** On-demand script injection, dynamic content script registration, injecting into the MAIN world to intercept page-level APIs, toggling CSS features.

---

## chrome.alarms

**Permission:** `"alarms"`

**Replaces:** `setTimeout` / `setInterval` which do not survive service worker suspension.

**Key methods:** `create`, `get`, `getAll`, `clear`, `clearAll`, `onAlarm`

```typescript
// Create a repeating alarm (minimum period: 1 minute in production)
await chrome.alarms.create("sync-data", {
  delayInMinutes: 0.5,     // first fire in 30 seconds
  periodInMinutes: 5,       // then every 5 minutes
});

// Create a one-shot alarm
await chrome.alarms.create("reminder", {
  when: Date.now() + 60 * 60 * 1000, // 1 hour from now
});

// Handle alarm fires
chrome.alarms.onAlarm.addListener((alarm) => {
  switch (alarm.name) {
    case "sync-data":
      syncDataWithServer();
      break;
    case "reminder":
      showReminder();
      break;
  }
});

// Clear a specific alarm
await chrome.alarms.clear("sync-data");

// List all active alarms
const all = await chrome.alarms.getAll();
console.log(`${all.length} alarms active`);
```

> **Minimum interval:** In packed (production) extensions, the minimum `periodInMinutes` is 1 minute. During development (unpacked), Chrome may allow shorter intervals for testing.

**When to use:** Periodic background tasks (sync, cleanup, polling), scheduled notifications, replacing `setInterval` which dies when the service worker suspends.

---

## chrome.notifications

**Permission:** `"notifications"`

**Key methods:** `create`, `update`, `clear`, `getAll`, `onClicked`, `onClosed`, `onButtonClicked`

```typescript
// Create a basic notification
const notifId = await chrome.notifications.create("order-shipped", {
  type: "basic",
  iconUrl: chrome.runtime.getURL("icons/icon-128.png"),
  title: "Order Shipped",
  message: "Your package #12345 is on its way!",
  priority: 2,
  buttons: [
    { title: "Track Package" },
    { title: "Dismiss" },
  ],
});

// Create a progress notification
await chrome.notifications.create("download-progress", {
  type: "progress",
  iconUrl: chrome.runtime.getURL("icons/icon-128.png"),
  title: "Downloading...",
  message: "report.pdf",
  progress: 45,
});

// Update progress
await chrome.notifications.update("download-progress", { progress: 90 });

// Handle notification click
chrome.notifications.onClicked.addListener((notifId) => {
  if (notifId === "order-shipped") {
    chrome.tabs.create({ url: "https://example.com/track/12345" });
    chrome.notifications.clear(notifId);
  }
});

// Handle button clicks
chrome.notifications.onButtonClicked.addListener((notifId, buttonIndex) => {
  if (notifId === "order-shipped" && buttonIndex === 0) {
    chrome.tabs.create({ url: "https://example.com/track/12345" });
  }
  chrome.notifications.clear(notifId);
});
```

**When to use:** User-facing alerts (new messages, task completion, reminders), progress indicators, actionable notifications with buttons.

---

## chrome.contextMenus

**Permission:** `"contextMenus"`

**Key methods:** `create`, `update`, `remove`, `removeAll`, `onClicked`

```typescript
// Create menus on install (service worker top-level or onInstalled)
chrome.runtime.onInstalled.addListener(() => {
  // Parent menu
  chrome.contextMenus.create({
    id: "main-menu",
    title: "My Extension",
    contexts: ["selection", "link", "page"],
  });

  // Child items
  chrome.contextMenus.create({
    id: "search-selected",
    parentId: "main-menu",
    title: 'Search "%s"', // %s = selected text
    contexts: ["selection"],
  });

  chrome.contextMenus.create({
    id: "save-link",
    parentId: "main-menu",
    title: "Save Link",
    contexts: ["link"],
  });

  chrome.contextMenus.create({
    id: "analyze-page",
    parentId: "main-menu",
    title: "Analyze This Page",
    contexts: ["page"],
  });
});

// Handle clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  switch (info.menuItemId) {
    case "search-selected":
      chrome.tabs.create({
        url: `https://google.com/search?q=${encodeURIComponent(info.selectionText!)}`,
      });
      break;
    case "save-link":
      saveLink(info.linkUrl!, tab?.title);
      break;
    case "analyze-page":
      analyzePage(tab!.id!);
      break;
  }
});
```

**Context types:** `"all"`, `"page"`, `"frame"`, `"selection"`, `"link"`, `"editable"`, `"image"`, `"video"`, `"audio"`, `"action"` (extension icon right-click).

**When to use:** Adding actions to the right-click menu, operating on selected text, links, or images.

---

## chrome.commands

**Permission:** None (declare in manifest `"commands"` key).

**Manifest declaration:**

```json
{
  "commands": {
    "toggle-sidebar": {
      "suggested_key": {
        "default": "Ctrl+Shift+S",
        "mac": "Command+Shift+S"
      },
      "description": "Toggle the sidebar"
    },
    "_execute_action": {
      "suggested_key": {
        "default": "Ctrl+Shift+E"
      }
    }
  }
}
```

```typescript
// background.ts
chrome.commands.onCommand.addListener(async (command, tab) => {
  switch (command) {
    case "toggle-sidebar":
      if (tab?.id) {
        await chrome.sidePanel.open({ tabId: tab.id });
      }
      break;
    // "_execute_action" automatically triggers chrome.action.onClicked — no handler needed here
  }
});

// List all registered commands and their shortcuts
const commands = await chrome.commands.getAll();
for (const cmd of commands) {
  console.log(`${cmd.name}: ${cmd.shortcut || "No shortcut assigned"}`);
}
```

> **Max 4 commands** can have suggested shortcuts. Users can customize shortcuts at `chrome://extensions/shortcuts`.

**When to use:** Keyboard shortcuts for power users, toggling extension features, quick actions without opening the popup.

---

## chrome.declarativeNetRequest

**Permission:** `"declarativeNetRequest"` (or `"declarativeNetRequestWithHostAccess"` for more flexible matching). Static rules also need `"declarativeNetRequest"` + a `"rule_resources"` entry in manifest.

**Key methods:** `updateDynamicRules`, `updateSessionRules`, `getDynamicRules`, `getSessionRules`, `updateEnabledRulesets`, `getMatchedRules`

### Static Rules (declared in manifest)

```json
{
  "declarative_net_request": {
    "rule_resources": [
      {
        "id": "default_rules",
        "enabled": true,
        "path": "rules/default.json"
      }
    ]
  }
}
```

```json
// rules/default.json
[
  {
    "id": 1,
    "priority": 1,
    "action": { "type": "block" },
    "condition": {
      "urlFilter": "||ads.example.com",
      "resourceTypes": ["script", "image", "xmlhttprequest"]
    }
  },
  {
    "id": 2,
    "priority": 1,
    "action": {
      "type": "redirect",
      "redirect": { "url": "https://new.example.com/page" }
    },
    "condition": {
      "urlFilter": "||old.example.com/page",
      "resourceTypes": ["main_frame"]
    }
  }
]
```

### Dynamic Rules (added/removed at runtime)

```typescript
// Block a domain dynamically
await chrome.declarativeNetRequest.updateDynamicRules({
  addRules: [
    {
      id: 1000,
      priority: 1,
      action: { type: chrome.declarativeNetRequest.RuleActionType.BLOCK },
      condition: {
        urlFilter: "||trackers.example.com",
        resourceTypes: [
          chrome.declarativeNetRequest.ResourceType.SCRIPT,
          chrome.declarativeNetRequest.ResourceType.XMLHTTPREQUEST,
        ],
      },
    },
  ],
  removeRuleIds: [1000], // remove old version first to avoid ID conflict
});

// Modify request headers
await chrome.declarativeNetRequest.updateDynamicRules({
  addRules: [
    {
      id: 2000,
      priority: 1,
      action: {
        type: chrome.declarativeNetRequest.RuleActionType.MODIFY_HEADERS,
        requestHeaders: [
          {
            header: "X-Custom-Header",
            operation: chrome.declarativeNetRequest.HeaderOperation.SET,
            value: "my-extension",
          },
        ],
      },
      condition: {
        urlFilter: "||api.example.com/*",
        resourceTypes: [chrome.declarativeNetRequest.ResourceType.XMLHTTPREQUEST],
      },
    },
  ],
  removeRuleIds: [2000],
});
```

**Rule limits:** 30,000 static rules (across all rulesets), 5,000 dynamic rules, 5,000 session rules.

**When to use:** Ad/tracker blocking, URL redirects, header modification, CORS workarounds -- all without reading request/response bodies.

---

## chrome.sidePanel

**Permission:** `"sidePanel"` (manifest key)

**Manifest:**

```json
{
  "side_panel": {
    "default_path": "sidepanel.html"
  }
}
```

**Key methods:** `setOptions`, `open`, `getOptions`, `getPanelBehavior`, `setPanelBehavior`

```typescript
// background.ts — show different side panels per site
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete") return;

  if (tab.url?.includes("github.com")) {
    await chrome.sidePanel.setOptions({
      tabId,
      path: "sidepanels/github-helper.html",
      enabled: true,
    });
  } else {
    await chrome.sidePanel.setOptions({
      tabId,
      path: "sidepanel.html",
      enabled: true,
    });
  }
});

// Open the side panel programmatically (must be in response to user action)
chrome.action.onClicked.addListener(async (tab) => {
  await chrome.sidePanel.open({ tabId: tab.id! });
});

// Control whether clicking the action icon opens the side panel
await chrome.sidePanel.setPanelBehavior({
  openPanelOnActionClick: true,
});
```

**When to use:** Persistent companion UI alongside web pages, chat assistants, reference panels, note-taking tools -- superior to popups when users need the panel to stay open.

---

## chrome.offscreen

**Permission:** None (but the API itself is restricted to MV3 service workers).

**Purpose:** Create hidden offscreen documents to use DOM APIs (Canvas, audio, clipboard, DOM parsing) that are unavailable in service workers.

**Key methods:** `createDocument`, `closeDocument`, `hasDocument`

```typescript
// background.ts
async function ensureOffscreenDocument() {
  const exists = await chrome.offscreen.hasDocument();
  if (!exists) {
    await chrome.offscreen.createDocument({
      url: chrome.runtime.getURL("offscreen.html"),
      reasons: [chrome.offscreen.Reason.DOM_PARSER],
      justification: "Parse HTML content for data extraction",
    });
  }
}

// Use the offscreen document to parse HTML
async function parseHTML(html: string): Promise<string[]> {
  await ensureOffscreenDocument();
  const response = await chrome.runtime.sendMessage({
    type: "PARSE_HTML",
    html,
  });
  return response.links;
}
```

```typescript
// offscreen.ts — runs in the offscreen document
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "PARSE_HTML") {
    const doc = new DOMParser().parseFromString(msg.html, "text/html");
    const links = Array.from(doc.querySelectorAll("a[href]")).map(
      (a) => (a as HTMLAnchorElement).href
    );
    sendResponse({ links });
  }
  return false;
});
```

**Offscreen reasons enum:** `TESTING`, `AUDIO_PLAYBACK`, `IFRAME_SCRIPTING`, `DOM_SCRAPING`, `DOM_PARSER`, `BLOBS`, `CLIPBOARD`, `DISPLAY_MEDIA`, `GEOLOCATION`, `WEB_RTC`, `LOCAL_STORAGE`, and others.

> **Only one offscreen document** can exist at a time per extension. Plan accordingly if you need multiple DOM capabilities.

**When to use:** DOM parsing, canvas rendering, audio playback, clipboard access, or any task requiring `document` or `window` APIs from the service worker.

---

## chrome.action

**Permission:** None (declared via `"action"` manifest key).

**Manifest:**

```json
{
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon-16.png",
      "32": "icons/icon-32.png",
      "48": "icons/icon-48.png",
      "128": "icons/icon-128.png"
    },
    "default_title": "My Extension"
  }
}
```

**Key methods:** `setIcon`, `setBadgeText`, `setBadgeBackgroundColor`, `setBadgeTextColor`, `setTitle`, `setPopup`, `enable`, `disable`, `onClicked`

```typescript
// Show unread count on badge
await chrome.action.setBadgeText({ text: "12" });
await chrome.action.setBadgeBackgroundColor({ color: "#DC2626" });
await chrome.action.setBadgeTextColor({ color: "#FFFFFF" });

// Per-tab badge
await chrome.action.setBadgeText({ text: "3", tabId: tab.id! });

// Disable the action for a specific tab (greys out icon)
await chrome.action.disable(tab.id!);

// Dynamic icon (e.g., active/inactive state)
await chrome.action.setIcon({
  path: {
    16: isActive ? "icons/active-16.png" : "icons/inactive-16.png",
    32: isActive ? "icons/active-32.png" : "icons/inactive-32.png",
  },
});

// onClicked only fires when there is NO default_popup
// Remove default_popup to use this:
chrome.action.onClicked.addListener(async (tab) => {
  // Toggle some feature
  const { enabled = false } = await chrome.storage.local.get("enabled");
  await chrome.storage.local.set({ enabled: !enabled });
  await chrome.action.setIcon({
    path: !enabled ? "icons/on.png" : "icons/off.png",
    tabId: tab.id!,
  });
});
```

**When to use:** Toolbar icon management, badge counters (unread messages, blocked items), toggling extension state, dynamic icons.

---

## chrome.runtime

**Permission:** None (always available).

**Key methods:** `getURL`, `getManifest`, `sendMessage`, `connect`, `onInstalled`, `onStartup`, `onSuspend`, `onMessage`, `onConnect`, `openOptionsPage`, `reload`, `id`

```typescript
// Get a URL to a bundled resource
const iconUrl = chrome.runtime.getURL("icons/icon-128.png");
// => "chrome-extension://<extension-id>/icons/icon-128.png"

// Read manifest data
const manifest = chrome.runtime.getManifest();
console.log(`v${manifest.version}`);

// Handle install and update
chrome.runtime.onInstalled.addListener((details) => {
  switch (details.reason) {
    case "install":
      chrome.tabs.create({ url: "onboarding.html" });
      break;
    case "update":
      console.log(`Updated from ${details.previousVersion}`);
      runMigrations(details.previousVersion!);
      break;
  }
});

// Runs every time Chrome starts (if extension is enabled)
chrome.runtime.onStartup.addListener(() => {
  console.log("Browser started, initializing...");
  initializeState();
});

// Service worker is about to be suspended
chrome.runtime.onSuspend.addListener(() => {
  console.log("Service worker suspending — clean up resources");
  // Close WebSocket connections, flush buffers, etc.
});
```

**When to use:** Extension lifecycle hooks (install, update, startup), resolving resource URLs, reading manifest info, opening options page.

---

## chrome.identity

**Permission:** `"identity"` (for `getAuthToken`). Web auth flow also needs the OAuth provider URL in `permissions` or `host_permissions`.

**Manifest (for Google OAuth):**

```json
{
  "permissions": ["identity"],
  "oauth2": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "scopes": ["https://www.googleapis.com/auth/userinfo.email"]
  }
}
```

**Key methods:** `getAuthToken`, `removeCachedAuthToken`, `launchWebAuthFlow`, `getProfileUserInfo`

### Google OAuth (getAuthToken)

```typescript
// Get a Google OAuth token (auto-prompts for consent)
try {
  const { token } = await chrome.identity.getAuthToken({ interactive: true });
  if (token) {
    const resp = await fetch("https://www.googleapis.com/oauth2/v2/userinfo", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const user = await resp.json();
    console.log("Logged in as:", user.email);
  }
} catch (err) {
  console.error("Auth failed:", err);
}

// Sign out — remove cached token and revoke it
async function signOut(token: string) {
  await chrome.identity.removeCachedAuthToken({ token });
  await fetch(`https://accounts.google.com/o/oauth2/revoke?token=${token}`);
}
```

### Non-Google OAuth (launchWebAuthFlow)

```typescript
// Generic OAuth2 flow (GitHub, Auth0, etc.)
const redirectUri = chrome.identity.getRedirectURL(); // https://<ext-id>.chromiumapp.org/
const clientId = "YOUR_GITHUB_CLIENT_ID";

const authUrl = new URL("https://github.com/login/oauth/authorize");
authUrl.searchParams.set("client_id", clientId);
authUrl.searchParams.set("redirect_uri", redirectUri);
authUrl.searchParams.set("scope", "repo user");
authUrl.searchParams.set("state", crypto.randomUUID());

try {
  const responseUrl = await chrome.identity.launchWebAuthFlow({
    url: authUrl.toString(),
    interactive: true,
  });

  // Extract the authorization code from the redirect
  const url = new URL(responseUrl!);
  const code = url.searchParams.get("code");

  // Exchange code for token via your backend (never expose client_secret in extension)
  const tokenResp = await fetch("https://your-backend.com/api/github/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  const { access_token } = await tokenResp.json();
  await chrome.storage.session.set({ githubToken: access_token });
} catch (err) {
  console.error("OAuth flow failed:", err);
}
```

**When to use:** Google account sign-in (getAuthToken), third-party OAuth providers (launchWebAuthFlow), accessing Google APIs, user profile information.

---

## API Availability by Context

Not every API is available in every extension context. Quick reference:

| API | Service Worker | Popup / Options | Content Script | Offscreen Doc |
|---|---|---|---|---|
| `chrome.tabs` | Yes | Yes | No | No |
| `chrome.scripting` | Yes | No | No | No |
| `chrome.alarms` | Yes | Yes | No | No |
| `chrome.notifications` | Yes | Yes | No | No |
| `chrome.contextMenus` | Yes | No | No | No |
| `chrome.commands` | Yes (onCommand) | Yes (getAll) | No | No |
| `chrome.declarativeNetRequest` | Yes | Yes | No | No |
| `chrome.sidePanel` | Yes | Yes | No | No |
| `chrome.offscreen` | Yes | No | No | N/A |
| `chrome.action` | Yes | Yes | No | No |
| `chrome.runtime` | Yes | Yes | Partial | Yes |
| `chrome.identity` | Yes | Yes | No | No |
| `chrome.storage` | Yes | Yes | local/sync (session w/ flag) | Yes |

---

## Required Permissions Summary

| API | Permission | Manifest Key |
|---|---|---|
| `chrome.tabs` | None (basic) / `"tabs"` (url/title) | `"permissions"` |
| `chrome.scripting` | `"scripting"` + host_permissions | `"permissions"` |
| `chrome.alarms` | `"alarms"` | `"permissions"` |
| `chrome.notifications` | `"notifications"` | `"permissions"` |
| `chrome.contextMenus` | `"contextMenus"` | `"permissions"` |
| `chrome.commands` | None | `"commands"` key in manifest |
| `chrome.declarativeNetRequest` | `"declarativeNetRequest"` | `"permissions"` + `"declarative_net_request"` |
| `chrome.sidePanel` | `"sidePanel"` | `"side_panel"` key in manifest |
| `chrome.offscreen` | None | N/A |
| `chrome.action` | None | `"action"` key in manifest |
| `chrome.runtime` | None | N/A |
| `chrome.identity` | `"identity"` | `"permissions"` + `"oauth2"` key |
| `chrome.storage` | `"storage"` | `"permissions"` |
