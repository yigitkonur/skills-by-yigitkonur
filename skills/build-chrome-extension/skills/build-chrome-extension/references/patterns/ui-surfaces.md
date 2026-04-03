# UI Surfaces Patterns (Manifest V3)

## Extension UI Surface Types

| Surface | Entry point | Lifecycle | Max dimensions | Min Chrome |
|---|---|---|---|---|
| Popup | `action.default_popup` | Destroyed on close/blur | ~800x600 | All MV3 |
| Options (embedded) | `options_ui.page` | Destroyed on tab close | ~680px width (iframe) | All MV3 |
| Options (full tab) | `options_ui` + `open_in_tab: true` | Destroyed on tab close | Full tab | All MV3 |
| Side panel | `side_panel.default_path` | Destroyed on panel close | ~400px wide (adjustable) | 114+ |
| DevTools panel | `devtools_page` | Destroyed when DevTools closes | Full panel | All MV3 |
| New tab override | `chrome_url_overrides.newtab` | Fresh on each new tab | Full tab | All MV3 |

**No UI surface preserves state automatically.** All in-memory state (React state, Vue refs,
Svelte stores) is destroyed on close. Persist to `chrome.storage`.

## Popup

```jsonc
{
  "action": {
    "default_popup": "popup.html",
    "default_icon": { "16": "icons/16.png", "32": "icons/32.png", "128": "icons/128.png" },
    "default_title": "My Extension"
  }
}
```

Destroyed when: user clicks outside, switches tabs, presses Escape, or calls `window.close()`.
No `beforeunload` guarantee — persist state proactively.

```html
<!DOCTYPE html>
<html><head>
  <meta charset="UTF-8">
  <link rel="stylesheet" href="popup.css"> <!-- no inline scripts in MV3 -->
</head><body>
  <div id="app"></div>
  <script type="module" src="popup.js"></script>
</body></html>
```

### State preservation pattern

```typescript
interface PopupState { selectedTab: string; searchQuery: string; }

async function restoreState(): Promise<PopupState> {
  const { popupState } = await chrome.storage.session.get("popupState");
  return popupState ?? { selectedTab: "home", searchQuery: "" };
}

function saveState(state: PopupState): void {
  chrome.storage.session.set({ popupState: state }); // fire-and-forget
}

document.addEventListener("DOMContentLoaded", async () => {
  const state = await restoreState();
  renderUI(state);
  document.getElementById("search")!.addEventListener("input", (e) => {
    saveState({ ...state, searchQuery: (e.target as HTMLInputElement).value });
  });
});
```

### Popup dimensions

- **Width:** max ~800px, min 25px. Recommended: 300-400px.
- **Height:** auto-sized to content up to ~600px; scrollbar after that.
- Cannot be resized by the user.

```css
body { width: 360px; min-height: 200px; max-height: 560px; overflow-y: auto; margin: 0; }
```

## Options Page

```jsonc
// Embedded (recommended) — renders in iframe on chrome://extensions
{ "options_ui": { "page": "options.html", "open_in_tab": false } }

// Full tab
{ "options_ui": { "page": "options.html", "open_in_tab": true } }
```

```typescript
// Open programmatically from popup or service worker
chrome.runtime.openOptionsPage();
```

```typescript
// options.ts — load/save/react to external changes
document.addEventListener("DOMContentLoaded", async () => {
  const { settings } = await chrome.storage.local.get("settings");
  populateForm(settings ?? { theme: "system", notifications: true });

  document.getElementById("save-btn")!.addEventListener("click", async () => {
    await chrome.storage.local.set({ settings: readFormValues() });
  });
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.settings) populateForm(changes.settings.newValue);
});
```

## Side Panel (Chrome 114+)

```jsonc
{ "permissions": ["sidePanel"], "side_panel": { "default_path": "sidepanel.html" } }
```

- Persists while open (longer-lived than popup). Destroyed on panel close.
- Each tab can have its own panel path. User can resize width.

```typescript
// Per-tab panel
chrome.sidePanel.setOptions({ tabId: tab.id, path: "sidepanel-detail.html", enabled: true });

// Disable for specific tab
chrome.sidePanel.setOptions({ tabId: tab.id, enabled: false });

// Open programmatically (must be from user gesture)
chrome.action.onClicked.addListener(async (tab) => {
  await chrome.sidePanel.open({ tabId: tab.id! });
});

// Or: clicking the action icon opens the side panel
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
```

```typescript
// sidepanel.ts — react to tab switches while panel is open
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  const tab = await chrome.tabs.get(activeInfo.tabId);
  loadContentForTab(tab);
});
```

Design for 320-500px width range (user-adjustable).

## DevTools Panel

```jsonc
{ "devtools_page": "devtools.html" }
```

```typescript
// devtools.ts — create panel (hidden devtools_page runs this)
chrome.devtools.panels.create("My Panel", "icons/16.png", "devtools-panel.html", (panel) => {
  panel.onShown.addListener((panelWindow) => initPanel(panelWindow));
  panel.onHidden.addListener(() => { /* panel hidden */ });
});

// Create sidebar in Elements panel
chrome.devtools.panels.elements.createSidebarPane("My Sidebar", (sidebar) => {
  sidebar.setPage("devtools-sidebar.html");
});

// Inspect the page
chrome.devtools.inspectedWindow.eval(
  "document.querySelectorAll('img').length",
  (result, err) => { if (!err) console.log(`${result} images`); },
);
const tabId = chrome.devtools.inspectedWindow.tabId;
```

## New Tab Override

```jsonc
{ "chrome_url_overrides": { "newtab": "newtab.html" } }
```

Fresh instance per new tab. Must load fast. Only one extension can override at a time.

## Framework Integration (Vite Multi-Entry)

```typescript
// vite.config.ts — works for React, Vue, Svelte, Solid
import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        popup: resolve(__dirname, "popup.html"),
        options: resolve(__dirname, "options.html"),
        sidepanel: resolve(__dirname, "sidepanel.html"),
        "service-worker": resolve(__dirname, "src/service-worker.ts"),
        "content-script": resolve(__dirname, "src/content-script.ts"),
      },
      output: { entryFileNames: "[name].js" },
    },
    outDir: "dist",
    emptyOutDir: true,
  },
});
```

### Framework entry points (all follow the same pattern)

```typescript
// React: src/popup/index.tsx
import { createRoot } from "react-dom/client";
import { App } from "./App";
createRoot(document.getElementById("app")!).render(<App />);

// Vue: src/popup/main.ts
import { createApp } from "vue";
import App from "./App.vue";
createApp(App).mount("#app");

// Svelte: src/popup/main.ts
import App from "./App.svelte";
new App({ target: document.getElementById("app")! });

// Solid: src/popup/index.tsx
import { render } from "solid-js/web";
import { App } from "./App";
render(() => <App />, document.getElementById("app")!);
```

### Reusable hook: useChromeStorage (React)

```typescript
import { useState, useEffect } from "react";

export function useChromeStorage<T>(key: string, defaultValue: T, area: "local" | "sync" | "session" = "local"): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(defaultValue);
  const storage = chrome.storage[area];

  useEffect(() => {
    storage.get(key).then((r) => { if (r[key] !== undefined) setValue(r[key]); });
    const listener = (changes: Record<string, chrome.storage.StorageChange>) => {
      if (changes[key]) setValue(changes[key].newValue);
    };
    chrome.storage.onChanged.addListener(listener);
    return () => chrome.storage.onChanged.removeListener(listener);
  }, [key, area]);

  return [value, (v: T) => { setValue(v); storage.set({ [key]: v }); }];
}
```

## Tailwind CSS in Extensions

```bash
npm install -D tailwindcss @tailwindcss/vite
```

```typescript
// vite.config.ts — add plugin
import tailwindcss from "@tailwindcss/vite";
export default defineConfig({ plugins: [tailwindcss()] });
```

### Content script CSS isolation

Tailwind classes can collide with page styles. Two solutions:

**Option A: Prefix** — `{ prefix: "ext-" }` in tailwind config. Usage: `ext-p-4 ext-bg-white`.

**Option B: Shadow DOM (recommended)** — inject compiled CSS into shadow root:

```typescript
function injectUI(): void {
  const host = document.createElement("div");
  const shadow = host.attachShadow({ mode: "closed" });
  const cssUrl = chrome.runtime.getURL("content-styles.css");
  fetch(cssUrl).then((r) => r.text()).then((css) => {
    const style = document.createElement("style");
    style.textContent = css;
    shadow.appendChild(style);
    const app = document.createElement("div");
    app.innerHTML = `<div class="p-4 bg-white rounded shadow-lg"><h2 class="text-lg font-bold">Panel</h2></div>`;
    shadow.appendChild(app);
  });
  document.body.appendChild(host);
}
```

## Communication from UI Surfaces to Background

All surfaces use the same APIs:

```typescript
// One-shot request/response
const result = await chrome.runtime.sendMessage({ type: "action", payload: {} });

// Long-lived connection (keeps SW alive while open)
const port = chrome.runtime.connect({ name: "popup" });
port.postMessage({ type: "subscribe" });
port.onMessage.addListener((msg) => { /* handle */ });

// Direct storage access (no messaging needed)
const { settings } = await chrome.storage.local.get("settings");

// Cross-surface sync via storage events
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.settings) applySettings(changes.settings.newValue);
});
```

| Scenario | Approach |
|---|---|
| Read/write user settings | Direct `chrome.storage` |
| Trigger background action (fetch, alarm) | `sendMessage` to SW |
| Stream real-time data to UI | `chrome.runtime.connect()` port |
| Sync state across popup + sidepanel | `chrome.storage.onChanged` |

## UI State Management: Debounced Auto-Save

```typescript
function createAutoSave<T>(key: string, debounceMs = 300) {
  let timer: ReturnType<typeof setTimeout>;
  return {
    save(state: T): void {
      clearTimeout(timer);
      timer = setTimeout(() => chrome.storage.session.set({ [key]: state }), debounceMs);
    },
    async load(): Promise<T | undefined> {
      const result = await chrome.storage.session.get(key);
      return result[key];
    },
    saveImmediate(state: T): void {
      clearTimeout(timer);
      chrome.storage.session.set({ [key]: state });
    },
  };
}
```

## Dark Mode / System Theme Detection

```typescript
function isDarkMode(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

// React to changes
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
  document.documentElement.classList.toggle("dark", e.matches);
});
```

### User-controlled theme with system fallback

```typescript
type Theme = "light" | "dark" | "system";

async function applyTheme(): Promise<void> {
  const { settings } = await chrome.storage.local.get("settings");
  const theme: Theme = settings?.theme ?? "system";
  const isDark = theme === "system"
    ? window.matchMedia("(prefers-color-scheme: dark)").matches
    : theme === "dark";
  document.documentElement.classList.toggle("dark", isDark);
}

document.addEventListener("DOMContentLoaded", applyTheme);
chrome.storage.onChanged.addListener((c) => { if (c.settings) applyTheme(); });
```

### CSS custom properties (framework-agnostic)

```css
:root {
  --bg-primary: #fff; --bg-secondary: #f5f5f5;
  --text-primary: #1a1a1a; --text-secondary: #666;
  --border: #e0e0e0; --accent: #4285f4;
}
:root.dark {
  --bg-primary: #1a1a1a; --bg-secondary: #2d2d2d;
  --text-primary: #e0e0e0; --text-secondary: #999;
  --border: #404040; --accent: #8ab4f8;
}
body { background: var(--bg-primary); color: var(--text-primary); }
```

Tailwind: set `darkMode: "class"` and use `dark:` variants.

## Surface Selection Decision Guide

| Need | Surface |
|---|---|
| Quick action, small UI | Popup |
| Persistent workspace beside page | Side panel |
| Full settings form | Options page |
| Developer inspection tools | DevTools panel |
| Dashboard / full app | New tab override or `chrome.tabs.create` |
| Background processing, no UI | Service worker (+ offscreen if DOM needed) |
| UI injected into a web page | Content script + Shadow DOM |
