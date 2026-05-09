# Chrome Extension Debugging Guide

Debug Chrome MV3 extension contexts using the right DevTools surface for each context.

Verified: 2026-05-09 against Chrome's official [Debug extensions](https://developer.chrome.com/docs/extensions/get-started/tutorial/debug) tutorial.

## Context Map

| Context | Where it runs | Primary debugging surface |
|---|---|---|
| Service worker | Extension background worker | `chrome://extensions` -> Inspect views -> service worker |
| Popup | Extension popup window | Right-click popup -> Inspect |
| Options page | Extension page/tab | Normal page DevTools |
| Content script | Target web page isolated world | Page DevTools -> Sources -> Content Scripts and console context dropdown |
| Side panel | Extension side panel | Right-click side panel -> Inspect |
| Offscreen document | Hidden extension document | Extension card inspect views when listed; otherwise inspect logs from linked extension context |

Avoid treating `chrome://serviceworker-internals` as the primary path. Current Chrome extension debugging docs use the Extensions Management page, service worker Inspect views, and DevTools Application -> Service Workers for service-worker status.

## Service Worker

Primary path:

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Locate the extension card.
4. Click the service worker link under **Inspect views**.
5. Use Console, Sources, Network, Application, and Service Workers panes.

Important caveat: inspecting the service worker keeps it active. Close DevTools before testing idle termination or restart resilience.

Use Application -> Service Workers when checking status:

1. Copy extension ID from the extension card.
2. Open `chrome-extension://EXTENSION_ID/manifest.json`.
3. Inspect the page.
4. Open Application -> Service Workers.
5. Start/stop the worker from the status controls.

## Manifest And Load Errors

Use the extension card first:

- invalid manifest keys often appear as load dialogs
- unknown permissions appear under the extension card's Errors button
- service-worker registration failures appear before DevTools can attach

Fast checks:

```bash
scripts/check-mv3-manifest.sh dist
scripts/preflight-extension.sh dist
```

Common failures:

| Error | Likely cause | Fix |
|---|---|---|
| `Could not load manifest` | invalid JSON or missing required field | parse manifest and check required fields |
| `Permission ... is unknown` | invalid permission spelling | use official permission names |
| `Service worker registration failed` | syntax/import error in worker | inspect extension Errors, fix top-level worker error |
| `Refused to execute inline script` | inline script or MV3 CSP violation | move script to packaged file |

## Popup, Options, And Side Panel

Popup:

1. Open popup from toolbar.
2. Right-click inside popup.
3. Select Inspect.

DevTools keeps the popup alive. For easier repeat debugging, open the popup path as a tab:

```typescript
const popupPath = chrome.runtime.getManifest().action?.default_popup;
if (popupPath) chrome.tabs.create({ url: chrome.runtime.getURL(popupPath) });
```

Options pages and side panels use normal DevTools inspection. Remember that popup and side-panel in-memory UI state disappears on close; persist state proactively.

## Content Scripts

1. Open DevTools on the target web page.
2. Use Sources -> Content Scripts to find extension files.
3. Use the console context dropdown to switch from `top` to the extension content-script context.
4. Check manifest `matches`, runtime injection targets, and host permissions when scripts do not appear.

Content-script errors can appear in the page's DevTools, not the extension card. Runtime errors emitted by popup or service worker contexts can appear on the extension card's Errors page.

## Messaging Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `Receiving end does not exist` | target content script not loaded or listener missing | verify match pattern, inject on demand, or wait for listener |
| `message port closed before a response was received` | async handler did not return `true` | return `true` synchronously and call `sendResponse` later |
| popup request disappears | popup closed before response | use storage-backed state or a port with disconnect handling |
| port disconnects | service worker idled or surface closed | reconnect and resume from persisted state |

## Network And Cross-Origin Requests

- Service-worker network requests appear in the service-worker DevTools Network tab.
- Popup/options/side-panel requests appear in their own DevTools Network tabs.
- Content-script `fetch()` follows the page origin; privileged cross-origin fetches should route through the service worker with constrained message payloads.
- To make extension-origin cross-origin `fetch()` work, declare the target origin in `host_permissions`.

## Storage Debugging

Quick console dump from an extension context:

```typescript
chrome.storage.local.get(null, (items) => console.table(items));
chrome.storage.sync.get(null, (items) => console.table(items));
chrome.storage.session.get(null, (items) => console.table(items));
```

Watch changes:

```typescript
chrome.storage.onChanged.addListener((changes, areaName) => {
  console.group(`[storage:${areaName}]`);
  for (const [key, change] of Object.entries(changes)) {
    console.log(key, change.oldValue, "->", change.newValue);
  }
  console.groupEnd();
});
```

## Common Error Map

| Error | Cause | Fix |
|---|---|---|
| `Extension context invalidated` | extension reloaded while a content script was running | guard API calls and handle reloads |
| `Cannot access a chrome:// URL` | injection attempted on restricted page | skip browser-internal URLs |
| `Quota exceeded for storage.sync` | 100 KB total or 8 KB item limit exceeded | move large data to `local` or IndexedDB |
| `chrome.scripting is undefined` | missing `scripting` permission or wrong context | add permission and call from extension context |
| `Access to fetch ... blocked by CORS` | content script or missing host permission | fetch from extension context with host permission |
| side panel does not open | missing `sidePanel` permission, wrong Chrome version, or no user gesture | add permission, check Chrome 116+ for `open()`, invoke from user action |

## Debug Checklist

1. Confirm the built output folder is loaded.
2. Run both bundled scripts against that folder.
3. Check extension card errors.
4. Inspect the correct context, not the nearest console.
5. Verify manifest permissions and host permissions.
6. Verify content-script `matches` and runtime injection target.
7. Verify async message handlers return `true`.
8. Close service-worker DevTools before idle/restart tests.
9. Reload the extension after rebuilding.
10. Remove and re-add the extension when generated output looks stale.
