# Permissions — Complete Reference

## Permissions vs Host Permissions vs Optional Permissions

| Category | Manifest Key | Granted At | User Prompt | Revocable by User |
|---|---|---|---|---|
| API permissions | `permissions` | Install time | Yes (if warning-triggering) | No (must uninstall) |
| Host permissions | `host_permissions` | Install time (may be withheld) | Yes | Yes (per-site via toolbar) |
| Optional API permissions | `optional_permissions` | Runtime (on user gesture) | Yes | Yes |
| Optional host permissions | `optional_host_permissions` | Runtime (on user gesture) | Yes | Yes |

**Key rule:** Chrome may auto-withhold `host_permissions` and let users grant them per-site. Design for this. Always check `chrome.permissions.contains()` before using host-dependent APIs.

---

## Complete Permissions Table

### Low Risk (No Warning)

| Permission | What It Grants | When to Use |
|---|---|---|
| `alarms` | Schedule recurring/one-time timers | Periodic background tasks, polling |
| `contextMenus` | Add items to right-click menu | Custom context menu actions |
| `idle` | Detect user idle/active/locked state | Pause activity when user is away |
| `notifications` | Show system notifications | Alerting users of events |
| `offscreen` | Create offscreen documents for DOM APIs | Audio playback, DOM parsing in service worker |
| `power` | Prevent display/system from sleeping | Long-running tasks (downloads, presentations) |
| `scripting` | Programmatically inject scripts/CSS | Dynamic content script injection |
| `sidePanel` | Use the side panel API | Persistent UI alongside web pages |
| `storage` | Use `chrome.storage` (local, sync, session) | Persisting extension state/settings |
| `system.cpu` | Read CPU info | System monitoring extensions |
| `system.display` | Read display info | Layout-aware extensions |
| `system.memory` | Read memory info | System monitoring extensions |
| `unlimitedStorage` | Remove 10 MB quota on `storage.local` | Large data caching |

### Medium Risk (Warning Displayed)

| Permission | What It Grants | Warning Text (Summary) | When to Use |
|---|---|---|---|
| `activeTab` | Temporary host access to the active tab on user gesture | "Access the current tab when you click" | One-click actions on current page |
| `bookmarks` | Read/write bookmarks | "Read and change your bookmarks" | Bookmark managers |
| `clipboardRead` | Read clipboard via `document.execCommand('paste')` | "Read data you copy and paste" | Clipboard utilities |
| `clipboardWrite` | Write clipboard via `document.execCommand('copy')` | "Modify data you copy and paste" | Clipboard utilities |
| `declarativeNetRequest` | Block/redirect/modify network requests via rules | "Block page content" | Ad blockers, privacy tools |
| `declarativeNetRequestWithHostAccess` | Same but requires matching host_permissions | (depends on hosts) | Targeted request modification |
| `desktopCapture` | Capture screen/window/tab content | "Capture content of your screen" | Screen recording, screenshots |
| `downloads` | Manage downloads | "Manage your downloads" | Download managers |
| `favicon` | Access site favicons via `chrome://favicon` | None (but restricted API) | Tab managers showing favicons |
| `geolocation` | Access user location | "Detect your physical location" | Location-aware features |
| `history` | Read/write browsing history | "Read your browsing history" | History search, analytics |
| `identity` | OAuth2 token management | "Know your email address" | Authentication flows |
| `management` | Manage other extensions | "Manage your extensions" | Extension managers |
| `nativeMessaging` | Communicate with native applications | "Communicate with native applications" | Native app integration |
| `pageCapture` | Save pages as MHTML | "Read and change all your data on all websites" | Page archiving |
| `privacy` | Control privacy settings | "Change privacy-related settings" | Privacy tools |
| `proxy` | Manage proxy settings | "Read and change all your data on all websites" | VPN/proxy extensions |
| `sessions` | Query/restore recently closed tabs/sessions | "Read your browsing history" | Session managers |
| `tabCapture` | Capture tab media streams | "Read and change all your data on all websites" | Tab recording |
| `tabGroups` | Interact with tab groups | "View and manage your tab groups" | Tab organization |
| `tabs` | Access `url`, `title`, `favIconUrl` on tabs | "Read your browsing history" | Tab search, management |
| `topSites` | Access most-visited sites | "Read a list of your most frequently visited websites" | New tab pages |
| `tts` | Text-to-speech synthesis | None | Accessibility, reading tools |
| `ttsEngine` | Implement a TTS engine | None | Custom speech engines |
| `webNavigation` | Observe navigation lifecycle events | "Read your browsing history" | Navigation tracking |

### High Risk (Intense Scrutiny)

| Permission | What It Grants | Warning | When to Use |
|---|---|---|---|
| `cookies` | Read/write cookies for host_permissions sites | "Read and change all your data on [sites]" | Authentication, session management |
| `debugger` | Attach Chrome DevTools Protocol | "Read and change all your data on all websites" | DevTools extensions only |
| `declarativeNetRequestFeedback` | See which DNR rules matched (debugging) | Same as `declarativeNetRequest` | Development/debugging only |
| `webRequest` | Observe network requests (read-only in MV3) | "Read and change all your data on all websites" | Network inspection (no blocking in MV3) |
| `<all_urls>` (host perm) | Access all URLs | "Read and change all your data on all websites" | Only when truly needed |
| `contentSettings` | Change per-site content settings | "Change site settings" | Privacy/content control |

---

## Host Permission Patterns

```jsonc
// Specific domain
"host_permissions": ["https://api.example.com/*"]

// All subdomains of a domain
"host_permissions": ["https://*.example.com/*"]

// Multiple specific domains
"host_permissions": [
  "https://api.example.com/*",
  "https://cdn.example.com/*"
]

// All HTTPS sites (triggers broad warning — avoid if possible)
"host_permissions": ["https://*/*"]

// All URLs (maximum warning — almost never appropriate)
"host_permissions": ["<all_urls>"]

// Specific path prefix
"host_permissions": ["https://example.com/api/*"]

// HTTP and HTTPS for a domain
"host_permissions": [
  "http://example.com/*",
  "https://example.com/*"
]
```

### Match Pattern Syntax

```
<scheme>://<host><path>

scheme: "http" | "https" | "*" | "file" | "ftp"
host:   "*" | "*." <domain> | <domain>
path:   "/" <any>
```

**Invalid patterns:**

```
"https://example.com"        // missing path — must be "https://example.com/*"
"https:/example.com/*"       // single slash
"example.com/*"              // missing scheme
"https://**.example.com/*"   // double wildcard not allowed
"https://exam*le.com/*"      // wildcard only valid at start of host
```

---

## activeTab: The Least-Privilege Alternative

`activeTab` grants temporary access to the current tab ONLY when the user triggers your extension via:
- Clicking the toolbar icon (action)
- Selecting a context menu item
- Using a keyboard shortcut
- Accepting an omnibox suggestion

```jsonc
// Instead of this (broad, scary warning):
{
  "permissions": ["tabs"],
  "host_permissions": ["<all_urls>"]
}

// Use this (minimal warning):
{
  "permissions": ["activeTab", "scripting"]
}
```

```typescript
// With activeTab + scripting, inject on user click
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;
  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.title,
  });
  console.log("Page title:", results[0]?.result);
});
```

`activeTab` access expires when the user navigates away or closes the tab.

---

## Requesting Optional Permissions at Runtime

```typescript
// Check if permission is already granted
const hasBookmarks = await chrome.permissions.contains({
  permissions: ["bookmarks"],
});

if (!hasBookmarks) {
  // MUST be called from a user gesture (click handler, etc.)
  const granted = await chrome.permissions.request({
    permissions: ["bookmarks"],
    origins: ["https://api.example.com/*"],
  });

  if (!granted) {
    console.log("User denied the permission");
    return;
  }
}

// Now safe to use the API
const bookmarks = await chrome.bookmarks.getTree();
```

```typescript
// Remove permissions you no longer need
await chrome.permissions.remove({
  permissions: ["bookmarks"],
  origins: ["https://api.example.com/*"],
});
```

```typescript
// Listen for permission changes (e.g., user revokes via toolbar)
chrome.permissions.onAdded.addListener((permissions) => {
  console.log("Granted:", permissions);
});

chrome.permissions.onRemoved.addListener((permissions) => {
  console.log("Revoked:", permissions);
  // Gracefully degrade feature
});
```

### What Can Be Optional

| Can be `optional_permissions` | Cannot be `optional_permissions` |
|---|---|
| `bookmarks`, `clipboardRead`, `clipboardWrite`, `cookies`, `downloads`, `geolocation`, `history`, `idle`, `notifications`, `tabs`, `topSites`, `webNavigation` | `debugger`, `declarativeNetRequest`, `devtools`, `management`, `nativeMessaging`, `proxy`, `tts`, `ttsEngine` |

A permission cannot appear in both `permissions` and `optional_permissions`.

---

## Permission Risk Matrix — Web Store Review

| Risk Tier | Triggers | Review Impact |
|---|---|---|
| Tier 1 (Low) | `storage`, `alarms`, `contextMenus`, `idle` | Auto-approved |
| Tier 2 (Medium) | `activeTab`, `scripting`, `notifications`, `tabs` | Brief review, standard justification |
| Tier 3 (High) | Broad `host_permissions`, `cookies`, `webRequest`, `history` | Extended review, detailed justification required |
| Tier 4 (Critical) | `<all_urls>`, `debugger`, `proxy`, `privacy`, `content settings` | Deep manual review, may be rejected without strong justification |

### What Increases Review Time

- Requesting `<all_urls>` or `*://*/*` host permissions
- Using `declarativeNetRequest` with broad URL patterns
- Combining `tabs` + broad host permissions (full browsing history exposure)
- Obfuscated/minified code (provide source maps or unminified source)
- `webRequest` + host permissions (even though MV3 limits it to observation)

---

## Permission Justification Guide (Web Store)

When submitting to the Chrome Web Store, you must justify each permission. Write clear, specific justifications.

### Bad Justifications (Will Be Rejected)

```
"tabs" — "We need it for the extension to work."
"<all_urls>" — "We need to access websites."
"cookies" — "Required for functionality."
```

### Good Justifications

```
"tabs" — "We display a searchable list of open tabs so users can quickly
switch between them. The 'tabs' permission is needed to read tab titles
and URLs for the search index."

"host_permissions: https://api.example.com/*" — "The extension fetches
user-specific settings from api.example.com and sends usage analytics.
No other domains are accessed."

"cookies" — "Users authenticate with example.com and the extension reads
the session cookie to maintain login state when making API requests on
behalf of the user. Only example.com cookies are accessed."
```

### Justification Template

```
Permission: [name]
Feature: [which user-facing feature requires this]
Scope: [what data is accessed and how narrowly]
Alternatives considered: [why a less-privileged approach doesn't work]
```

---

## Best Practices for Least-Privilege

### 1. Prefer `activeTab` Over `host_permissions`

If you only need access when the user clicks your icon, `activeTab` is always better.

### 2. Use `optional_permissions` for Non-Core Features

```jsonc
{
  "permissions": ["storage"],                    // always needed
  "optional_permissions": ["bookmarks", "history"]  // only if user enables feature
}
```

### 3. Narrow Host Permissions

```jsonc
// Bad: too broad
"host_permissions": ["<all_urls>"]

// Better: specific domains
"host_permissions": ["https://api.example.com/*"]

// Best: use optional_host_permissions for secondary sites
"host_permissions": ["https://api.example.com/*"],
"optional_host_permissions": ["https://api.backup-service.com/*"]
```

### 4. Drop Permissions When No Longer Needed

```typescript
// After completing a one-time import from bookmarks
await chrome.permissions.remove({ permissions: ["bookmarks"] });
```

### 5. Check Before Using

```typescript
async function withPermission<T>(
  permission: string,
  action: () => Promise<T>
): Promise<T | null> {
  const has = await chrome.permissions.contains({
    permissions: [permission],
  });
  if (!has) {
    const granted = await chrome.permissions.request({
      permissions: [permission],
    });
    if (!granted) return null;
  }
  return action();
}

// Usage
const tree = await withPermission("bookmarks", () =>
  chrome.bookmarks.getTree()
);
```

---

## Common Permission Mistakes

### Mistake 1: Requesting `tabs` When You Only Need Tab IDs

```typescript
// tabs permission is NOT needed for:
chrome.tabs.query({ active: true, currentWindow: true }); // returns tab id, status, etc.
chrome.tabs.create({ url: "https://example.com" });
chrome.tabs.remove(tabId);

// tabs permission IS needed for:
// accessing tab.url, tab.title, tab.favIconUrl
```

### Mistake 2: Using `host_permissions` Instead of `activeTab`

If your extension only operates when the user clicks the toolbar icon, replace:
```jsonc
"host_permissions": ["<all_urls>"]
```
with:
```jsonc
"permissions": ["activeTab"]
```

### Mistake 3: Putting Everything in `permissions`

Move non-essential permissions to `optional_permissions` to reduce install friction and warning severity.

### Mistake 4: Forgetting Host Permissions for `cookies` / `webRequest`

`cookies` and `webRequest` require corresponding `host_permissions` for the domains you want to access. Without host permissions, the API calls silently return empty results.

```jsonc
{
  "permissions": ["cookies"],
  "host_permissions": ["https://example.com/*"]  // required for cookies API to work
}
```

### Mistake 5: Not Handling Permission Revocation

Users can revoke `host_permissions` via the toolbar icon menu. Always check and degrade gracefully.

```typescript
chrome.permissions.onRemoved.addListener(({ permissions, origins }) => {
  if (origins?.includes("https://api.example.com/*")) {
    // Disable features that depend on this origin
    disableApiIntegration();
    showReEnablePrompt();
  }
});
```

### Mistake 6: Requesting `declarativeNetRequest` Without `host_permissions`

For rules that modify requests to specific domains, you need matching host permissions. Without them, rules targeting those domains will silently fail.

```jsonc
{
  "permissions": ["declarativeNetRequest"],
  "host_permissions": ["*://*.example.com/*"]
}
```

### Mistake 7: Using `file://` Scheme in Host Permissions

`file://` URLs require users to manually enable "Allow access to file URLs" on the extension's details page. Even if declared, it won't work without the user toggle. Prefer `optional_host_permissions` and check at runtime.

---

## Quick Decision Tree

```
Need to access tab content?
  Only when user clicks toolbar icon? → activeTab + scripting
  On specific domains automatically? → host_permissions (specific domains)
  On every page automatically? → host_permissions (<all_urls>) — justify heavily

Need to call a Chrome API?
  Core feature? → permissions
  Secondary feature? → optional_permissions

Need to read/modify network requests?
  Block/redirect by rules? → declarativeNetRequest
  Just observe? → webRequest (read-only in MV3)

Need cookies?
  → permissions: ["cookies"] + host_permissions for the domain
```
