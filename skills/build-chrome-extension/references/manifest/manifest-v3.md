# Manifest V3 — Complete Reference

## manifest.json Structure

Every Chrome extension requires a `manifest.json` at the root. MV3 uses `"manifest_version": 3`.

### Required vs Optional Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `manifest_version` | Yes | `3` | Must be `3` for MV3 |
| `name` | Yes | `string` (max 75 chars) | Extension display name |
| `version` | Yes | `string` (1-4 dot-separated integers) | e.g. `"1.2.3"` |
| `description` | Recommended | `string` (max 132 chars) | Shown in Web Store and `chrome://extensions` |
| `icons` | Recommended | `object` | See Icons section |
| `action` | Optional | `object` | Toolbar button config |
| `background` | Optional | `object` | Service worker registration |
| `content_scripts` | Optional | `array` | Scripts injected into web pages |
| `permissions` | Optional | `array<string>` | API permissions |
| `host_permissions` | Optional | `array<string>` | URL match patterns for host access |
| `optional_permissions` | Optional | `array<string>` | Permissions requestable at runtime |
| `optional_host_permissions` | Optional | `array<string>` | Host permissions requestable at runtime |
| `content_security_policy` | Optional | `object` | CSP overrides |
| `web_accessible_resources` | Optional | `array<object>` | Resources accessible from web pages |
| `commands` | Optional | `object` | Keyboard shortcut bindings |
| `declarative_net_request` | Optional | `object` | Network request rules |
| `devtools_page` | Optional | `string` | DevTools panel HTML page |
| `options_page` | Optional | `string` | Options page (full tab) |
| `options_ui` | Optional | `object` | Options page (embedded popup) |
| `side_panel` | Optional | `object` | Side panel configuration |
| `omnibox` | Optional | `object` | Address bar keyword trigger |
| `externally_connectable` | Optional | `object` | Cross-extension / webpage messaging |
| `minimum_chrome_version` | Optional | `string` | Minimum supported Chrome version |
| `default_locale` | Conditional | `string` | Required if `_locales/` directory exists |
| `key` | Optional | `string` | Fixed extension ID for development |
| `author` | Optional | `string` or `object` | Author info |
| `homepage_url` | Optional | `string` | Extension homepage |
| `short_name` | Optional | `string` (max 12 chars) | Short name for limited space |
| `version_name` | Optional | `string` | Human-readable version (e.g. `"1.0 beta"`) |
| `incognito` | Optional | `"spanning"` or `"split"` | Incognito mode behavior |
| `storage` | Optional | `object` | Managed storage schema |
| `update_url` | Optional | `string` | Self-hosted update URL |
| `export` | Optional | `object` | Shared module export config |
| `import` | Optional | `array` | Shared module imports |

### Version String Rules

```
"version": "1"          // valid
"version": "1.2"        // valid
"version": "1.2.3"      // valid
"version": "1.2.3.4"    // valid (max 4 segments)
"version": "1.2.3.4.5"  // INVALID — max 4 segments
"version": "1.02.3"     // INVALID — no leading zeros
```

Each segment: integer 0–65535. Compared left-to-right: `1.10.0 > 1.9.0`.

---

## Icons Specification

Provide multiple sizes. Chrome picks the closest and scales.

```jsonc
{
  "icons": {
    "16": "icons/icon-16.png",   // favicon, context menu
    "32": "icons/icon-32.png",   // Windows taskbar
    "48": "icons/icon-48.png",   // extensions management page
    "128": "icons/icon-128.png"  // Web Store, installation dialog
  }
}
```

| Size | Where Used |
|---|---|
| 16x16 | Favicon in extension pages, context menus |
| 32x32 | Windows taskbar shortcut |
| 48x48 | `chrome://extensions` management page |
| 128x128 | Chrome Web Store listing, install prompt |

**Format:** PNG required. SVG is not supported in manifest icons. Transparent backgrounds are fine.

**Action icons** are separate from manifest icons:

```jsonc
{
  "action": {
    "default_icon": {
      "16": "toolbar/icon-16.png",
      "24": "toolbar/icon-24.png",
      "32": "toolbar/icon-32.png"
    }
  }
}
```

---

## Background Service Worker

MV3 replaces persistent background pages with a service worker.

```jsonc
{
  "background": {
    "service_worker": "background.js",  // single built entry point
    "type": "module"                     // enables ES module imports
  }
}
```

**Key constraints:**
- Exactly one `service_worker` file (no array)
- Must be at the extension root (not in a subdirectory unless bundled)
- `"type": "module"` required for `import`/`export` syntax
- No DOM access — no `document`, no `window`, no `XMLHttpRequest`
- Terminates after ~30 seconds of inactivity (5 minutes for active event processing)

If you author the service worker in TypeScript, bundle or transpile it so the loadable extension manifest still points at the emitted `.js` file.

```typescript
// src/background.ts — source entry point that builds to background.js
import { setupContextMenus } from "./lib/menus.js";
import { handleMessages } from "./lib/messages.js";

chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    setupContextMenus();
  }
});

chrome.runtime.onMessage.addListener(handleMessages);
```

---

## Action Configuration

The `action` field controls the toolbar button (replaces both `browser_action` and `page_action` from MV2).

```jsonc
{
  "action": {
    "default_icon": {
      "16": "icons/action-16.png",
      "32": "icons/action-32.png"
    },
    "default_title": "My Extension",     // tooltip text
    "default_popup": "popup/index.html"   // popup HTML file
  }
}
```

If `default_popup` is omitted, clicking the icon fires `chrome.action.onClicked`. You cannot have both a popup and an `onClicked` listener.

---

## Content Scripts

```jsonc
{
  "content_scripts": [
    {
      "matches": ["https://*.example.com/*"],
      "exclude_matches": ["https://admin.example.com/*"],
      "css": ["styles/content.css"],
      "js": ["content/main.js"],
      "run_at": "document_idle",          // default
      "all_frames": false,                // default: top frame only
      "match_about_blank": false,         // default
      "match_origin_as_fallback": false,  // for blob:/data: URLs
      "world": "ISOLATED"                 // default; or "MAIN"
    }
  ]
}
```

| `run_at` Value | When |
|---|---|
| `document_start` | After CSS loads, before DOM or other scripts |
| `document_end` | After DOM complete, before images/subframes |
| `document_idle` | After `document_end`, on idle or `window.onload` (default) |

| `world` Value | Behavior |
|---|---|
| `ISOLATED` | Separate JS context, shared DOM. Cannot access page JS variables. Default. |
| `MAIN` | Same context as the page. Can access page JS. No Chrome API access. |

---

## Content Security Policy (MV3)

MV3 enforces a strict default CSP. You can relax it only within boundaries.

### Default CSP (applied if you omit the field)

```
script-src 'self';
object-src 'self';
```

### What You Can Override

```jsonc
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'; style-src 'self' 'unsafe-inline'",
    "sandbox": "sandbox allow-scripts; script-src 'self' https://cdn.example.com"
  }
}
```

### MV3 CSP Restrictions

| Directive | Allowed | Blocked |
|---|---|---|
| `script-src` | `'self'`, `'wasm-unsafe-eval'` | `'unsafe-eval'`, `'unsafe-inline'`, remote URLs, `data:`, `blob:` |
| `object-src` | `'self'` | Remote origins |
| `style-src` | `'self'`, `'unsafe-inline'` | Remote origins |
| Remote code | Never for extension pages | `eval()`, `new Function()`, remote `<script src>` |
| Sandbox pages | Relaxed — remote scripts allowed | Still no `'unsafe-eval'` in non-sandbox pages |

**Sandboxed pages** (`sandbox` key) can load remote scripts but have no Chrome API access and cannot communicate via `chrome.runtime.sendMessage` — use `window.postMessage` with the parent frame instead.

```typescript
// Using wasm-unsafe-eval for WebAssembly
// manifest.json: "extension_pages": "script-src 'self' 'wasm-unsafe-eval'; object-src 'self'"
const wasmModule = await WebAssembly.instantiateStreaming(
  fetch(chrome.runtime.getURL("module.wasm"))
);
```

---

## Web Accessible Resources

In MV3, web accessible resources require explicit origin matching (no blanket access).

```jsonc
{
  "web_accessible_resources": [
    {
      "resources": ["images/*.png", "styles/injected.css"],
      "matches": ["https://*.example.com/*"]
    },
    {
      "resources": ["content/injected-ui.js"],
      "matches": ["<all_urls>"]
    },
    {
      "resources": ["shared/data.json"],
      "extension_ids": ["abcdefghijklmnopabcdefghijklmnop"]
    }
  ]
}
```

| Property | Type | Purpose |
|---|---|---|
| `resources` | `string[]` | Glob patterns for files to expose |
| `matches` | `string[]` | URL patterns of web pages that can access these resources |
| `extension_ids` | `string[]` | Other extensions that can access these resources |
| `use_dynamic_url` | `boolean` | If `true`, resource URLs rotate to prevent fingerprinting |

**Access from web pages:**

```typescript
// In content script — get the URL to a resource
const imageUrl = chrome.runtime.getURL("images/logo.png");
// => chrome-extension://EXTENSION_ID/images/logo.png
```

---

## Internationalization (_locales)

### Directory Structure

```
extension/
  _locales/
    en/
      messages.json
    es/
      messages.json
    ja/
      messages.json
  manifest.json       // must have "default_locale": "en"
```

### messages.json Format

```jsonc
// _locales/en/messages.json
{
  "extensionName": {
    "message": "My Extension",
    "description": "The display name of the extension"
  },
  "extensionDescription": {
    "message": "Does useful things",
    "description": "Description shown in the Web Store"
  },
  "greeting": {
    "message": "Hello, $USER$! You have $COUNT$ messages.",
    "description": "Greeting with placeholders",
    "placeholders": {
      "user": {
        "content": "$1",
        "example": "Alice"
      },
      "count": {
        "content": "$2",
        "example": "3"
      }
    }
  }
}
```

### Using i18n

```jsonc
// manifest.json — use __MSG_key__ syntax
{
  "name": "__MSG_extensionName__",
  "description": "__MSG_extensionDescription__",
  "default_locale": "en"
}
```

```typescript
// In TypeScript code
const name = chrome.i18n.getMessage("extensionName");
const greeting = chrome.i18n.getMessage("greeting", ["Alice", "3"]);
// => "Hello, Alice! You have 3 messages."

// In CSS
/* Use __MSG_@@bidi_dir__ for bidirectional text */
body {
  direction: __MSG_@@bidi_dir__;
}
```

```html
<!-- In HTML — automatic substitution not supported; use JS -->
<span id="greeting"></span>
<script>
  document.getElementById("greeting")!.textContent =
    chrome.i18n.getMessage("greeting", ["Alice", "3"]);
</script>
```

### Predefined Messages

| Message | Value |
|---|---|
| `@@extension_id` | The extension's ID |
| `@@ui_locale` | Current UI locale (e.g., `"en_US"`) |
| `@@bidi_dir` | `"ltr"` or `"rtl"` |
| `@@bidi_reversed_dir` | Opposite of `@@bidi_dir` |
| `@@bidi_start_edge` | `"left"` for LTR, `"right"` for RTL |
| `@@bidi_end_edge` | `"right"` for LTR, `"left"` for RTL |

---

## Commands (Keyboard Shortcuts)

```jsonc
{
  "commands": {
    "_execute_action": {
      "suggested_key": {
        "default": "Ctrl+Shift+Y",
        "mac": "Command+Shift+Y"
      },
      "description": "Open the popup"
    },
    "toggle-feature": {
      "suggested_key": {
        "default": "Alt+Shift+T"
      },
      "description": "Toggle the main feature"
    },
    "run-silently": {
      "description": "Run background task (no default shortcut)"
    }
  }
}
```

### Reserved Command Names

| Name | Behavior |
|---|---|
| `_execute_action` | Triggers `action.onClicked` or opens the popup |
| `_execute_side_panel` | Opens the side panel |

### Key Combination Rules

- Must include a modifier: `Ctrl` / `Alt` / `Command` (Mac) / `MacCtrl` (Mac Ctrl key)
- `Ctrl` maps to `Command` on Mac unless you explicitly use `MacCtrl`
- Media keys (`MediaPlayPause`, `MediaNextTrack`, `MediaPrevTrack`, `MediaStop`) can be used without modifiers
- Maximum 4 shortcuts per extension
- Users can remap shortcuts at `chrome://extensions/shortcuts`

```typescript
// Listen for custom command
chrome.commands.onCommand.addListener((command: string) => {
  if (command === "toggle-feature") {
    // handle toggle
  }
});
```

---

## DeclarativeNetRequest Rule Resources

```jsonc
{
  "declarative_net_request": {
    "rule_resources": [
      {
        "id": "blocking_rules",
        "enabled": true,
        "path": "rules/block.json"
      },
      {
        "id": "redirect_rules",
        "enabled": false,
        "path": "rules/redirect.json"
      }
    ]
  },
  "permissions": ["declarativeNetRequest"],
  "host_permissions": ["*://*.example.com/*"]
}
```

### Rule File Format

```jsonc
// rules/block.json
[
  {
    "id": 1,
    "priority": 1,
    "action": { "type": "block" },
    "condition": {
      "urlFilter": "||tracker.example.com",
      "resourceTypes": ["script", "xmlhttprequest"]
    }
  },
  {
    "id": 2,
    "priority": 2,
    "action": {
      "type": "redirect",
      "redirect": { "extensionPath": "/blocked.html" }
    },
    "condition": {
      "urlFilter": "||ads.example.com",
      "resourceTypes": ["main_frame", "sub_frame"]
    }
  }
]
```

### Limits

| Limit | Value |
|---|---|
| Static rules per extension | 330,000 (across all rulesets) |
| Enabled static rulesets | 50 |
| Total static rulesets | 100 |
| Dynamic rules | 30,000 |
| Session rules | 5,000 |
| Regex rules (static) | 1,000 |
| Regex rules (dynamic) | 1,000 |

---

## Complete Full-Featured Manifest Example

```jsonc
{
  "manifest_version": 3,
  "name": "__MSG_extensionName__",
  "version": "2.1.0",
  "version_name": "2.1.0 stable",
  "description": "__MSG_extensionDescription__",
  "default_locale": "en",
  "minimum_chrome_version": "116",
  "author": { "email": "dev@example.com" },
  "homepage_url": "https://example.com/extension",

  "icons": {
    "16": "icons/icon-16.png",
    "32": "icons/icon-32.png",
    "48": "icons/icon-48.png",
    "128": "icons/icon-128.png"
  },

  "action": {
    "default_icon": {
      "16": "icons/action-16.png",
      "32": "icons/action-32.png"
    },
    "default_title": "My Extension",
    "default_popup": "popup/index.html"
  },

  "background": {
    "service_worker": "background.js",
    "type": "module"
  },

  "content_scripts": [
    {
      "matches": ["https://*.example.com/*"],
      "js": ["content/main.js"],
      "css": ["content/styles.css"],
      "run_at": "document_idle",
      "world": "ISOLATED"
    }
  ],

  "permissions": [
    "storage",
    "alarms",
    "notifications",
    "contextMenus",
    "declarativeNetRequest"
  ],
  "host_permissions": [
    "https://*.example.com/*"
  ],
  "optional_permissions": [
    "tabs",
    "bookmarks"
  ],
  "optional_host_permissions": [
    "https://*.other-site.com/*"
  ],

  "options_ui": {
    "page": "options/index.html",
    "open_in_tab": false
  },

  "side_panel": {
    "default_path": "sidepanel/index.html"
  },

  "commands": {
    "_execute_action": {
      "suggested_key": {
        "default": "Ctrl+Shift+E",
        "mac": "Command+Shift+E"
      },
      "description": "Open extension popup"
    },
    "quick-action": {
      "suggested_key": { "default": "Alt+Q" },
      "description": "Run quick action"
    }
  },

  "declarative_net_request": {
    "rule_resources": [
      {
        "id": "primary_rules",
        "enabled": true,
        "path": "rules/primary.json"
      }
    ]
  },

  "web_accessible_resources": [
    {
      "resources": ["content/injected.css", "images/*"],
      "matches": ["https://*.example.com/*"]
    }
  ],

  "content_security_policy": {
    "extension_pages": "script-src 'self' 'wasm-unsafe-eval'; object-src 'self'"
  },

  "externally_connectable": {
    "matches": ["https://*.example.com/*"]
  },

  "incognito": "spanning",

  "storage": {
    "managed_schema": "schema/managed.json"
  }
}
```

---

## Quick Validation Checklist

1. `manifest_version` is exactly `3` (not `"3"`, not `2`)
2. `version` uses only integers and dots, max 4 segments, no leading zeros
3. `name` is under 75 characters
4. `description` is under 132 characters
5. `background.service_worker` points to a single file (not an array)
6. `content_scripts[].matches` uses valid match patterns (scheme + host + path)
7. Icons are PNG files at the correct sizes
8. `default_locale` is set if and only if `_locales/` directory exists
9. No `'unsafe-eval'` or remote script sources in `content_security_policy.extension_pages`
10. `web_accessible_resources` uses object format with `matches` or `extension_ids` (not the MV2 flat array)
