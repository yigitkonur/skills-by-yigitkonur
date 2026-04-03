# Messaging API Reference

## Architecture Overview

Manifest V3 extensions have four isolated execution contexts that communicate exclusively through message passing:

```
+------------+     chrome.runtime      +--------------+
|   Popup    | <---------------------> |  Background  |
| (UI page)  |     sendMessage /       | (Service SW) |
+------------+     onMessage           +--------------+
                                            ^  |
                          chrome.tabs       |  | chrome.runtime
                          .sendMessage      |  | .sendMessage
                          (to content)      |  | (from content)
                                            |  v
                                       +----------------+
                                       | Content Script |
                                       | (page context) |
                                       +----------------+
                                            ^  |
                           window           |  | window
                           .postMessage     |  | .postMessage
                                            |  v
                                       +----------------+
                                       |   Web Page     |
                                       +----------------+
```

**Key rules:**
- Popup, options page, and side panel share the extension origin -- they can use `chrome.runtime.sendMessage` to talk to each other and the background service worker.
- Content scripts run in the web page's process but in an isolated world. The background must use `chrome.tabs.sendMessage(tabId, ...)` to reach them.
- Web pages cannot use `chrome.runtime` unless the extension declares `externally_connectable`.

---

## One-Time Messages (Fire and Forget / Request-Response)

### Sending from Popup / Options / Side Panel to Background

```typescript
// popup.ts — send a request and await a response
const response = await chrome.runtime.sendMessage({
  type: "GET_USER_DATA",
  payload: { userId: "abc-123" },
});
console.log("Background replied:", response);
```

### Listening in the Background Service Worker

```typescript
// background.ts
chrome.runtime.onMessage.addListener(
  (
    message: { type: string; payload?: unknown },
    sender: chrome.runtime.MessageSender,
    sendResponse: (response?: unknown) => void
  ) => {
    if (message.type === "GET_USER_DATA") {
      // Synchronous reply — just call sendResponse
      sendResponse({ name: "Alice", plan: "pro" });
      return false; // signal: response already sent
    }

    if (message.type === "FETCH_REMOTE") {
      // Async reply — MUST return true to keep the channel open
      fetchFromApi(message.payload as string)
        .then((data) => sendResponse({ ok: true, data }))
        .catch((err) => sendResponse({ ok: false, error: err.message }));
      return true; // <-- critical: keeps sendResponse alive
    }
  }
);
```

> **The `return true` rule:** If your handler does any asynchronous work before calling `sendResponse`, you **must** `return true` from the listener synchronously. Otherwise Chrome closes the message channel and the sender receives `undefined`.

### Sending from Background to a Specific Content Script

```typescript
// background.ts — target a specific tab
async function notifyContentScript(tabId: number, data: unknown) {
  try {
    const response = await chrome.tabs.sendMessage(tabId, {
      type: "HIGHLIGHT_ELEMENT",
      payload: data,
    });
    console.log("Content script responded:", response);
  } catch (err) {
    // Tab may have been closed or content script not injected
    console.warn(`Tab ${tabId} unreachable:`, err);
  }
}
```

### Listening in a Content Script

```typescript
// content.ts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "HIGHLIGHT_ELEMENT") {
    const el = document.querySelector(message.payload.selector);
    if (el) {
      (el as HTMLElement).style.outline = "3px solid red";
      sendResponse({ found: true });
    } else {
      sendResponse({ found: false });
    }
  }
  return false;
});
```

---

## Type-Safe Messaging Pattern

Define a message map so every `type` has a known request and response shape:

```typescript
// types/messages.ts
export interface MessageMap {
  GET_USER_DATA: {
    request: { userId: string };
    response: { name: string; plan: string } | null;
  };
  SAVE_SETTINGS: {
    request: { theme: "light" | "dark"; fontSize: number };
    response: { ok: boolean };
  };
  PING: {
    request: undefined;
    response: "pong";
  };
}

export type MessageType = keyof MessageMap;

export interface TypedMessage<T extends MessageType = MessageType> {
  type: T;
  payload: MessageMap[T]["request"];
}

// Typed sender
export async function sendTypedMessage<T extends MessageType>(
  type: T,
  payload: MessageMap[T]["request"]
): Promise<MessageMap[T]["response"]> {
  return chrome.runtime.sendMessage({ type, payload });
}

// Typed sender to content script
export async function sendToTab<T extends MessageType>(
  tabId: number,
  type: T,
  payload: MessageMap[T]["request"]
): Promise<MessageMap[T]["response"]> {
  return chrome.tabs.sendMessage(tabId, { type, payload });
}
```

Usage in the popup:

```typescript
import { sendTypedMessage } from "../types/messages";

const user = await sendTypedMessage("GET_USER_DATA", { userId: "abc-123" });
// user is typed as { name: string; plan: string } | null
```

Usage in the background listener with exhaustive handling:

```typescript
import type { MessageMap, MessageType, TypedMessage } from "../types/messages";

type Handler<T extends MessageType> = (
  payload: MessageMap[T]["request"],
  sender: chrome.runtime.MessageSender
) => Promise<MessageMap[T]["response"]> | MessageMap[T]["response"];

const handlers: { [T in MessageType]?: Handler<T> } = {
  GET_USER_DATA: async ({ userId }) => {
    const data = await db.getUser(userId);
    return data ?? null;
  },
  SAVE_SETTINGS: async (settings) => {
    await chrome.storage.local.set({ settings });
    return { ok: true };
  },
  PING: () => "pong",
};

chrome.runtime.onMessage.addListener((msg: TypedMessage, sender, sendResponse) => {
  const handler = handlers[msg.type] as Handler<typeof msg.type> | undefined;
  if (!handler) return false;

  const result = handler(msg.payload, sender);
  if (result instanceof Promise) {
    result.then(sendResponse).catch((e) => sendResponse({ error: e.message }));
    return true; // async — keep channel open
  }
  sendResponse(result);
  return false;
});
```

---

## Long-Lived Connections (Ports)

Use ports when you need a persistent bidirectional channel -- for example, streaming progress updates from background to popup.

### Opening a Port from Popup

```typescript
// popup.ts
const port = chrome.runtime.connect({ name: "progress-stream" });

port.onMessage.addListener((msg: { percent: number; status: string }) => {
  updateProgressBar(msg.percent);
  updateStatusText(msg.status);
});

port.onDisconnect.addListener(() => {
  console.log("Background disconnected the port");
  if (chrome.runtime.lastError) {
    console.error("Disconnect reason:", chrome.runtime.lastError.message);
  }
});

// Send a command over the port
port.postMessage({ action: "START_SYNC" });
```

### Accepting Ports in the Background

```typescript
// background.ts
chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== "progress-stream") return;

  port.onMessage.addListener(async (msg) => {
    if (msg.action === "START_SYNC") {
      for (let i = 0; i <= 100; i += 10) {
        // Guard: popup may close mid-stream
        if (!port) return;
        try {
          port.postMessage({ percent: i, status: `Syncing ${i}%` });
        } catch {
          return; // port disconnected
        }
        await sleep(200);
      }
    }
  });

  port.onDisconnect.addListener(() => {
    console.log("Popup closed the port");
  });
});
```

### Port to Content Script

```typescript
// background.ts — open a port to a content script
const port = chrome.tabs.connect(tabId, { name: "dom-watcher" });
port.postMessage({ action: "START_OBSERVING", selector: "#feed" });

// content.ts — accept the port
chrome.runtime.onConnect.addListener((port) => {
  if (port.name === "dom-watcher") {
    port.onMessage.addListener((msg) => {
      if (msg.action === "START_OBSERVING") {
        observeDOM(msg.selector, (mutations) => {
          port.postMessage({ type: "DOM_CHANGE", count: mutations.length });
        });
      }
    });
  }
});
```

### Port Lifecycle Rules

| Event | Cause | What happens |
|---|---|---|
| `port.onDisconnect` fires on one side | The other side called `port.disconnect()` | Channel closed, further `postMessage` throws |
| `port.onDisconnect` fires automatically | Popup/tab closed | Same as above |
| Service worker suspends | Chrome idles the SW | All ports disconnect; SW wakes on next `onConnect` |
| `chrome.runtime.lastError` set on disconnect | Error during disconnect | Check inside `onDisconnect` handler |

---

## External Messaging

### Receiving Messages from Web Pages

Declare allowed origins in `manifest.json`:

```json
{
  "externally_connectable": {
    "matches": ["https://example.com/*", "https://*.example.com/*"]
  }
}
```

Web page sends:

```typescript
// On the web page (not extension code)
const extensionId = "abcdefghijklmnopabcdefghijklmnop";
chrome.runtime.sendMessage(extensionId, { type: "LOGIN_TOKEN", token: "xyz" }, (resp) => {
  console.log("Extension replied:", resp);
});
```

Background receives via `onMessageExternal`:

```typescript
// background.ts
chrome.runtime.onMessageExternal.addListener((message, sender, sendResponse) => {
  // sender.url contains the page URL — validate it
  if (!sender.url?.startsWith("https://example.com")) {
    sendResponse({ error: "unauthorized" });
    return;
  }
  if (message.type === "LOGIN_TOKEN") {
    handleExternalLogin(message.token).then(sendResponse);
    return true;
  }
});
```

### Native Messaging

Communicate with a native host application (requires `nativeMessaging` permission and a native host manifest installed on the OS).

```typescript
// background.ts
const port = chrome.runtime.connectNative("com.example.myhost");

port.onMessage.addListener((msg) => {
  console.log("Native host sent:", msg);
});

port.onDisconnect.addListener(() => {
  console.log("Native host disconnected:", chrome.runtime.lastError?.message);
});

port.postMessage({ command: "encrypt", data: "secret" });
```

Native host manifest (`com.example.myhost.json`):

```json
{
  "name": "com.example.myhost",
  "description": "My native host",
  "path": "/usr/local/bin/my-native-host",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://abcdefghijklmnopabcdefghijklmnop/"]
}
```

---

## Content Script ↔ Web Page Messaging

Content scripts share the DOM but not the JS context with the web page. Use `window.postMessage`:

```typescript
// content.ts — relay from page to background
window.addEventListener("message", (event) => {
  if (event.source !== window) return;
  if (event.data?.source !== "MY_EXT_PAGE") return;

  chrome.runtime.sendMessage({
    type: "PAGE_EVENT",
    payload: event.data.payload,
  });
});

// Inject a script that posts messages from the page world
const script = document.createElement("script");
script.src = chrome.runtime.getURL("page-bridge.js");
document.documentElement.appendChild(script);
```

```typescript
// page-bridge.js (runs in page MAIN world)
document.addEventListener("my-ext-event", (e: CustomEvent) => {
  window.postMessage(
    { source: "MY_EXT_PAGE", payload: e.detail },
    window.location.origin
  );
});
```

Alternatively, in Manifest V3 you can use `chrome.scripting.executeScript` with `world: "MAIN"` to inject directly into the page context without a separate file.

---

## Common Messaging Failures and Fixes

| Symptom | Cause | Fix |
|---|---|---|
| `sendMessage` callback receives `undefined` | Listener did not call `sendResponse`, or async handler did not `return true` | Ensure every code path calls `sendResponse`; return `true` for async |
| `"Could not establish connection. Receiving end does not exist."` | No listener registered, content script not injected in target tab, or extension context invalidated | Check that the content script matches the tab URL; use `chrome.scripting.executeScript` to inject on demand |
| `"The message port closed before a response was received."` | Async handler forgot `return true`; or the sender context (popup) closed before reply arrived | Add `return true`; for popup, consider using ports instead |
| Messages from popup stop after popup closes | Popup is destroyed when closed; one-time messages in flight are lost | Use ports and handle `onDisconnect`, or send fire-and-forget messages and poll storage for results |
| `chrome.runtime.lastError` set after `sendMessage` | Extension was reloaded/updated while message was in flight | Wrap in try/catch; check `chrome.runtime.id` before sending |
| Content script receives messages meant for other content scripts | `onMessage` fires in all content scripts across all tabs | Always filter by `message.type`; background should target with `chrome.tabs.sendMessage(specificTabId, ...)` |
| Port immediately disconnects in service worker | Service worker was suspended between `connect` and first `postMessage` | Handle `onDisconnect` gracefully; use alarms or one-time messages for infrequent communication |
| `sendMessage` to content script fails on `chrome://` or `edge://` pages | Extensions cannot inject content scripts into browser-internal pages | Check `tab.url` before sending; skip restricted URLs |
| Response is silently swallowed | Multiple `onMessage` listeners registered; only the first to `sendResponse` wins | Use a single dispatcher listener with a handler map |
| Serialization error: "could not be cloned" | Attempting to send non-serializable data (functions, DOM nodes, class instances) | Only send JSON-serializable plain objects, arrays, strings, numbers, booleans, and null |

---

## Best Practices Summary

1. **Always define a `type` field** on every message. Route with a `switch` or handler map -- never rely on the shape of the payload alone.
2. **Use the typed messaging wrapper** above to get compile-time safety on both sender and receiver.
3. **Prefer one-time messages** for simple request/response. Use ports only when you need streaming or high-frequency updates.
4. **Handle service worker suspension.** Ports disconnect when the SW goes idle. Design for reconnection or fall back to one-time messages with storage-based state.
5. **Validate `sender`** in `onMessage` and `onMessageExternal`. Check `sender.id` (extension ID), `sender.url`, or `sender.tab` to prevent spoofing.
6. **Never assume the other end exists.** Wrap `sendMessage` in try/catch. Check for `chrome.runtime.lastError` in callbacks.
7. **Avoid large payloads** in messages (soft limit ~64 MB, but large messages block the event loop). For large data, write to storage and send a key.
