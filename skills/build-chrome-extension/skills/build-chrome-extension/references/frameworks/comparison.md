# Chrome Extension Framework Comparison (Manifest V3)

## Framework Comparison Table

| Feature | WXT | Plasmo | CRXJS Vite | Vanilla (Vite/Webpack) |
|---------|-----|--------|------------|----------------------|
| **Setup complexity** | Low (`npm create wxt@latest`) | Low (`npm create plasmo`) | Medium (Vite plugin config) | High (manual config) |
| **TypeScript support** | Built-in, first-class | Built-in, first-class | Via Vite config | Manual tsconfig setup |
| **HMR (popup/options)** | Yes | Yes | Yes | Manual setup |
| **HMR (content scripts)** | Yes (auto-reload) | Yes (CSUI live reload) | Partial | No |
| **HMR (service worker)** | Auto-reload on change | Auto-reload on change | Auto-reload on change | Manual reload |
| **Multi-browser support** | Chrome, Firefox, Edge, Safari | Chrome, Firefox, Edge | Chrome only | Manual per-browser |
| **React support** | Yes | Yes (primary framework) | Yes | Manual |
| **Vue support** | Yes | Community | Yes | Manual |
| **Svelte support** | Yes | Community | Yes | Manual |
| **Solid support** | Yes | Community | No | Manual |
| **Manifest generation** | Automatic from file conventions | Automatic from package.json | From vite config | Manual |
| **Content Script UI** | Manual | Built-in (CSUI) | Manual | Manual |
| **Storage utilities** | `wxt/storage` API | `@plasmohq/storage` | None | Manual |
| **Message passing** | `wxt/messaging` API | `@plasmohq/messaging` | None | Manual |
| **GitHub stars (approx)** | ~5k | ~10k | ~2k | N/A |
| **npm weekly downloads** | ~15k | ~20k | ~8k | N/A |
| **First release** | 2023 | 2022 | 2022 | N/A |
| **Maintenance status** | Active | Active | Slower updates | N/A |
| **Learning curve** | Low | Low | Medium | High |
| **Bundle size overhead** | Minimal | Small (runtime) | Minimal | None |
| **Automated testing** | Vitest integration | Vitest/Jest | Vitest | Manual |

---

## WXT Quick Start

### Setup

```bash
npm create wxt@latest my-extension
cd my-extension
npm install
npm run dev  # starts dev mode with auto-reload
```

### Project Structure

```
my-extension/
├── wxt.config.ts          # WXT configuration
├── src/
│   ├── entrypoints/
│   │   ├── background.ts      # Service worker (auto-detected)
│   │   ├── popup/
│   │   │   ├── index.html      # Popup HTML
│   │   │   ├── main.tsx        # Popup entry (React)
│   │   │   └── style.css
│   │   ├── options/
│   │   │   ├── index.html
│   │   │   └── main.tsx
│   │   └── content.ts         # Content script (auto-detected)
│   ├── components/
│   ├── utils/
│   └── assets/
├── public/
│   └── icon/
│       ├── 16.png
│       ├── 32.png
│       ├── 48.png
│       └── 128.png
└── package.json
```

### Key Configuration

```typescript
// wxt.config.ts
import { defineConfig } from "wxt";

export default defineConfig({
  srcDir: "src",
  manifest: {
    name: "My Extension",
    permissions: ["storage", "activeTab"],
    host_permissions: ["https://api.example.com/*"],
  },
  runner: {
    startUrls: ["https://example.com"], // open on dev start
  },
});
```

### File Convention Magic

WXT auto-generates manifest entries based on file paths:

| File Path | Manifest Entry |
|-----------|---------------|
| `entrypoints/background.ts` | `background.service_worker` |
| `entrypoints/popup/index.html` | `action.default_popup` |
| `entrypoints/options/index.html` | `options_page` |
| `entrypoints/content.ts` | `content_scripts[0]` |
| `entrypoints/sidepanel/index.html` | `side_panel.default_path` |
| `entrypoints/devtools.html` | `devtools_page` |

### Content Script Definition

```typescript
// src/entrypoints/content.ts
export default defineContentScript({
  matches: ["*://*.example.com/*"],
  runAt: "document_idle",
  main() {
    console.log("Content script loaded on", window.location.href);
  },
});
```

### Storage API

```typescript
// src/utils/storage.ts
import { storage } from "wxt/storage";

// Define typed storage items
const enabled = storage.defineItem<boolean>("sync:enabled", { fallback: true });
const blocklist = storage.defineItem<string[]>("local:blocklist", { fallback: [] });

// Usage
const isEnabled = await enabled.getValue();
await enabled.setValue(false);

// Watch for changes
enabled.watch((newValue) => {
  console.log("Enabled changed to", newValue);
});
```

### Messaging API

```typescript
// src/utils/messages.ts
import { defineExtensionMessaging } from "wxt/messaging";

interface ProtocolMap {
  getCount: { input: void; output: number };
  increment: { input: number; output: number };
}

export const { sendMessage, onMessage } = defineExtensionMessaging<ProtocolMap>();

// background.ts
onMessage("getCount", () => count);
onMessage("increment", ({ data }) => {
  count += data;
  return count;
});

// popup.tsx
const count = await sendMessage("getCount", undefined);
```

---

## Plasmo Quick Start

### Setup

```bash
npm create plasmo -- --with-react  # or --with-vue, --with-svelte
cd my-plasmo-ext
npm install
npm run dev
```

### Project Structure

```
my-plasmo-ext/
├── package.json               # Manifest fields live here
├── src/
│   ├── background.ts          # Service worker
│   ├── popup.tsx              # Popup (React component, auto-wrapped)
│   ├── options.tsx            # Options page
│   ├── contents/
│   │   └── example.tsx        # Content Script UI (CSUI)
│   ├── tabs/
│   │   └── settings.tsx       # Custom tab pages
│   └── components/
├── assets/
│   └── icon.png               # Auto-resized for all sizes
└── .plasmo/                   # Generated build artifacts
```

### Manifest via package.json

```json
{
  "name": "My Extension",
  "version": "1.0.0",
  "manifest": {
    "permissions": ["storage", "activeTab"],
    "host_permissions": ["https://api.example.com/*"]
  }
}
```

### Content Script UI (CSUI) — Plasmo's Killer Feature

Plasmo renders React/Vue/Svelte components directly into web pages inside a Shadow DOM:

```typescript
// src/contents/price-badge.tsx
import type { PlasmoCSConfig, PlasmoGetInlineAnchor } from "plasmo";

export const config: PlasmoCSConfig = {
  matches: ["https://www.amazon.com/dp/*"],
  css: ["../style.css"],
};

// Anchor the component next to a specific element
export const getInlineAnchor: PlasmoGetInlineAnchor = () =>
  document.querySelector("#priceblock_ourprice");

// The component renders inside Shadow DOM (isolated styles)
export default function PriceBadge() {
  const [tracked, setTracked] = useState(false);

  return (
    <button
      onClick={() => setTracked(!tracked)}
      style={{ marginLeft: 8, padding: "4px 8px" }}
    >
      {tracked ? "Tracking" : "Track Price"}
    </button>
  );
}
```

### Plasmo Storage Hook

```typescript
// src/popup.tsx
import { useStorage } from "@plasmohq/storage/hook";

export default function Popup() {
  const [enabled, setEnabled] = useStorage("enabled", true);
  const [count] = useStorage("count", 0);

  return (
    <div>
      <label>
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
        />
        Enabled
      </label>
      <p>Count: {count}</p>
    </div>
  );
}
```

### Plasmo Messaging

```typescript
// src/background/messages/get-count.ts
import type { PlasmoMessaging } from "@plasmohq/messaging";

const handler: PlasmoMessaging.MessageHandler = async (req, res) => {
  const count = await getCountFromStorage();
  res.send({ count });
};

export default handler;

// src/popup.tsx — calling the handler
import { sendToBackground } from "@plasmohq/messaging";

const response = await sendToBackground({ name: "get-count" });
console.log(response.count);
```

---

## CRXJS Vite Quick Start

### Setup

```bash
npm create vite@latest my-crx-ext -- --template react-ts
cd my-crx-ext
npm install @crxjs/vite-plugin@beta
```

### Vite Config

```typescript
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { crx } from "@crxjs/vite-plugin";
import manifest from "./manifest.json";

export default defineConfig({
  plugins: [react(), crx({ manifest })],
});
```

### Manifest (Standard JSON)

```json
{
  "manifest_version": 3,
  "name": "My CRXJS Extension",
  "version": "1.0.0",
  "action": {
    "default_popup": "src/popup/index.html"
  },
  "background": {
    "service_worker": "src/background.ts",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["https://*.example.com/*"],
      "js": ["src/content/index.ts"]
    }
  ],
  "permissions": ["storage"]
}
```

CRXJS treats those manifest paths as source entrypoints during the Vite build. Edit `src/...`, run the CRXJS/Vite build, and load only `dist/` in Chrome. Do not point Chrome at `src/` or expect the source paths in `manifest.json` to be loadable as-is.

### Project Structure

```
my-crx-ext/
├── manifest.json              # Standard Chrome manifest
├── vite.config.ts
├── src/
│   ├── background.ts
│   ├── popup/
│   │   ├── index.html
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── content/
│   │   └── index.ts
│   └── options/
│       ├── index.html
│       └── main.tsx
└── public/
    └── icons/
```

### HMR Behavior

CRXJS provides HMR for popup and options pages out of the box. Content scripts get full-page reload. The service worker auto-reloads when changed.

---

## Vanilla Setup (Vite)

### Setup

```bash
npm create vite@latest my-ext -- --template vanilla-ts
cd my-ext
npm install -D @types/chrome
npm run build
```

Load `dist/` in `chrome://extensions` after the first successful build.

If your `tsconfig.json` uses `compilerOptions.types`, add `"chrome"` so the global extension API types resolve.

### Vite Config for Multi-Entry Extension

```typescript
// vite.config.ts
import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  build: {
    outDir: "dist",
    rollupOptions: {
      input: {
        popup: resolve(__dirname, "src/popup/index.html"),
        options: resolve(__dirname, "src/options/index.html"),
        background: resolve(__dirname, "src/background/index.ts"),
        content: resolve(__dirname, "src/content/index.ts"),
      },
      output: {
        entryFileNames: "[name]/index.js",
        chunkFileNames: "chunks/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash].[ext]",
      },
    },
    // Service worker cannot use ES modules in MV3 without type: "module"
    // For broad compatibility, consider bundling as IIFE:
    // target: "esnext",
  },
  publicDir: "public", // copies manifest.json and icons
});
```

`publicDir: "public"` is what makes the build loadable: Vite copies `public/manifest.json`, icons, and other static assets into `dist/` unchanged. Put popup HTML in the configured Rollup inputs and keep copied assets in `public/`.

With this setup, `public/manifest.json` should reference built paths like `popup/index.html`, `background/index.js`, and `content/index.js`. Do not point a hand-written manifest at `src/...`.

**Import-path rule:** with WXT/CRXJS/Vite bundling, write normal TypeScript source imports and let the bundler rewrite output paths. If you replace the bundler with plain `tsc`/Node ESM, add `.js` to relative runtime imports yourself or stay on a bundler-backed setup.

**Shared-repo rule:** if this extension lives inside a larger TypeScript monorepo, keep a dedicated extension `tsconfig` or package boundary so unrelated app code does not break the extension build.

### Manual manifest.json

```json
{
  "manifest_version": 3,
  "name": "My Vanilla Extension",
  "version": "1.0.0",
  "description": "A hand-crafted Chrome extension",
  "action": {
    "default_popup": "popup/index.html",
    "default_icon": {
      "16": "icons/icon-16.png",
      "48": "icons/icon-48.png",
      "128": "icons/icon-128.png"
    }
  },
  "background": {
    "service_worker": "background/index.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["https://*.example.com/*"],
      "js": ["content/index.js"],
      "run_at": "document_idle"
    }
  ],
  "permissions": ["storage", "activeTab"],
  "icons": {
    "16": "icons/icon-16.png",
    "48": "icons/icon-48.png",
    "128": "icons/icon-128.png"
  }
}
```

### Dev Reload Script

Since vanilla has no built-in HMR for extensions:

```typescript
// src/dev-reload.ts — only included in dev builds
const RELOAD_INTERVAL = 1000;

async function checkForChanges() {
  try {
    const response = await fetch("http://localhost:5173/__dev_timestamp");
    const { timestamp } = await response.json();
    const stored = await chrome.storage.session.get("__dev_timestamp");
    if (stored.__dev_timestamp && stored.__dev_timestamp !== timestamp) {
      chrome.runtime.reload();
    }
    await chrome.storage.session.set({ __dev_timestamp: timestamp });
  } catch {
    // Dev server not running
  }
}

setInterval(checkForChanges, RELOAD_INTERVAL);
```

---

## Decision Guide: When to Use Each Framework

```
Start here:
│
├─ Do you need multi-browser support (Firefox, Safari)?
│   ├─ Yes → WXT (best cross-browser support)
│   └─ No → continue
│
├─ Do you need to render React/Vue/Svelte UI inside web pages (content script UI)?
│   ├─ Yes → Plasmo (CSUI is best-in-class)
│   └─ No → continue
│
├─ Are you already using Vite with React/Vue?
│   ├─ Yes → CRXJS Vite Plugin (minimal config change)
│   └─ No → continue
│
├─ Do you want a batteries-included framework with storage + messaging APIs?
│   ├─ Yes →
│   │   ├─ Prefer file-convention-based config → WXT
│   │   └─ Prefer package.json-based config → Plasmo
│   └─ No → continue
│
├─ Do you want full control with no framework overhead?
│   ├─ Yes → Vanilla + Vite
│   └─ No → WXT (safest default)
│
└─ Default recommendation: WXT
    - Most flexible, best docs, active community
    - Works for simple and complex extensions
    - Easy migration path from vanilla
```

### Quick Recommendation Table

| Scenario | Recommended |
|----------|-------------|
| New project, unsure of needs | WXT |
| React popup + content script with UI overlay | Plasmo |
| Existing Vite project, adding extension | CRXJS Vite |
| Simple extension, minimal deps | Vanilla + Vite |
| Firefox + Chrome support required | WXT |
| Enterprise/internal tool, max control | Vanilla + Webpack/Vite |
| Learning Chrome extensions for the first time | WXT or Plasmo |
| Migrating from Manifest V2 | WXT (has migration guide) |

---

## Framework Migration Paths

### Vanilla → WXT

1. Move entry files to `src/entrypoints/` following WXT conventions
2. Remove custom Vite/Webpack config (WXT handles it)
3. Delete `manifest.json` — configure in `wxt.config.ts`
4. Replace raw `chrome.storage` calls with `wxt/storage` (optional)
5. Replace `chrome.runtime.sendMessage` with `wxt/messaging` (optional)

### Vanilla → Plasmo

1. Move popup component to `src/popup.tsx`
2. Move background script to `src/background.ts`
3. Move content scripts to `src/contents/`
4. Move manifest fields to `package.json` under `"manifest"` key
5. Delete manual build config

### Plasmo → WXT

1. Rename `src/contents/*.tsx` to `src/entrypoints/content*.ts` (rewrite CSUI as manual Shadow DOM)
2. Move `package.json` manifest fields to `wxt.config.ts`
3. Replace `@plasmohq/storage` with `wxt/storage`
4. Replace `@plasmohq/messaging` with `wxt/messaging`

### CRXJS → WXT

1. Remove `@crxjs/vite-plugin` from `vite.config.ts`
2. Move entries to `src/entrypoints/`
3. Delete `manifest.json` — configure in `wxt.config.ts`
4. Install `wxt` and update build scripts

---

## Build and Output Structure

Treat the processed manifest inside the generated output directory as authoritative. The source tree varies by framework, but Chrome only loads the built output folder.

### WXT Output

```
.output/
├── chrome-mv3-dev/          # Dev build used by `wxt dev`
│   ├── manifest.json        # Auto-generated
│   ├── background.js
│   ├── content-scripts/
│   │   └── content.js
│   ├── popup.html
│   ├── popup.js
│   └── icons/
├── chrome-mv3/              # Production build used by `wxt build`
│   ├── manifest.json        # Auto-generated
│   ├── background.js
│   ├── content-scripts/
│   │   └── content.js
│   ├── popup.html
│   ├── popup.js
│   └── icons/
├── firefox-mv2/             # Firefox build (auto-generated)
│   ├── manifest.json        # Converted to MV2
│   └── ...
└── firefox-mv3/             # Firefox MV3 build
```

### Plasmo Output

```
build/
├── chrome-mv3-dev/          # Dev build
│   ├── manifest.json
│   ├── static/
│   │   └── background/
│   │       └── index.js
│   ├── popup.html
│   └── content-scripts/
├── chrome-mv3-prod/         # Production build
│   └── ...
```

### CRXJS Output

```
dist/
├── manifest.json            # Processed manifest
├── src/
│   ├── popup/
│   │   └── index.html
│   ├── background.js
│   └── content/
│       └── index.js
├── assets/
└── vendor/                  # CRXJS runtime (HMR client in dev)
```

### Vanilla Vite Output

```
dist/
├── manifest.json            # Copied from public/
├── popup/
│   └── index.html
├── background/
│   └── index.js
├── content/
│   └── index.js
├── chunks/                  # Shared code chunks
├── assets/
└── icons/
```

---

## Hot Module Replacement Setup

### WXT — Zero Config

HMR works out of the box:

```bash
npm run dev  # Starts dev server with HMR
```

- Popup/options: true HMR (component state preserved)
- Content scripts: auto-reload on change
- Service worker: auto-reload on change

### Plasmo — Zero Config

```bash
npm run dev  # Starts dev server with HMR
```

- Popup/options: true HMR
- CSUI content scripts: HMR with Shadow DOM preservation
- Service worker: auto-reload

### CRXJS — Zero Config (via plugin)

```bash
npx vite  # Standard Vite dev command
```

- Popup/options: true HMR via Vite
- Content scripts: page reload on change
- Service worker: auto-reload

### Vanilla — Manual Setup

For Vite, add a watch mode with extension reload:

```json
{
  "scripts": {
    "dev": "vite build --watch --mode development",
    "dev:reload": "npm run dev & node scripts/watch-reload.js"
  }
}
```

```typescript
// scripts/watch-reload.ts
import chokidar from "chokidar";
import { WebSocketServer } from "ws";

const wss = new WebSocketServer({ port: 8777 });

chokidar.watch("dist/", { ignoreInitial: true }).on("all", () => {
  wss.clients.forEach((client) => client.send("reload"));
});

// In your background.ts (dev only):
// const ws = new WebSocket("ws://localhost:8777");
// ws.onmessage = () => chrome.runtime.reload();
```

For full HMR in vanilla setups, consider switching to WXT or CRXJS — the manual approach only provides full-reload, not stateful HMR.
