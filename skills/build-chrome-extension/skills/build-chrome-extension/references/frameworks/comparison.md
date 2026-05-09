# Chrome MV3 Framework Selection

Choose a framework for Chrome Manifest V3 output only. Firefox, Safari, Edge policy deployment, and generic browser-extension compatibility are out of scope for `build-chrome-extension`.

## Default Choice

Use **WXT** for new greenfield Chrome MV3 extensions unless repo evidence points elsewhere.

Why:

- MV3 conventions are first-class.
- Entry points map cleanly to service worker, popup, options, side panel, and content scripts.
- Dev output and production output are explicit.
- TypeScript, storage helpers, messaging helpers, and auto-reload reduce boilerplate.

## Selection Table

| Situation | Choose | Reason |
|---|---|---|
| New Chrome MV3 extension with no repo preference | WXT | Best default balance of conventions and control |
| Popup/options/sidebar plus normal content scripts | WXT | Keeps extension architecture explicit |
| React/Vue/Svelte UI injected into pages as content-script UI | Plasmo | Content-script UI is its strongest lane |
| Existing Vite app needs Chrome extension output | CRXJS | Smallest build-system change |
| Existing custom build or explicit no-framework requirement | Vanilla + Vite | Maximum control, more manual manifest/build work |
| Cross-browser Firefox/Safari target | Out of scope | Route to a cross-browser extension skill or project-specific guidance |

## WXT

Use WXT for most new Chrome MV3 work.

### Setup

```bash
npm create wxt@latest my-extension
cd my-extension
npm install
npm run dev
```

### Chrome output

| Mode | Load in Chrome |
|---|---|
| Development | `.output/chrome-mv3-dev/` |
| Production | `.output/chrome-mv3/` |

### Expected shape

```text
src/
  entrypoints/
    background.ts
    content.ts
    popup/
      index.html
      main.tsx
    options/
      index.html
      main.tsx
    sidepanel/
      index.html
      main.tsx
wxt.config.ts
public/
  icon/
```

### Agent rules

- Put Chrome permissions and manifest fields in `wxt.config.ts`.
- Treat generated `manifest.json` inside `.output/chrome-mv3*` as authoritative.
- Load `.output/chrome-mv3-dev/` during development and `.output/chrome-mv3/` for production checks.
- Run the bundled manifest and preflight scripts against the generated output, not source.

## Plasmo

Use Plasmo when page-injected UI is the main product surface and the repo accepts Plasmo conventions.

### Setup

```bash
npm create plasmo -- --with-react
cd my-plasmo-ext
npm install
npm run dev
```

### Chrome output

| Mode | Load in Chrome |
|---|---|
| Development | `build/chrome-mv3-dev/` |
| Production | `build/chrome-mv3-prod/` |

### Best fit

- React-first popup/options work.
- Content-script UI mounted into pages.
- Shadow DOM UI isolation without hand-rolling every injection detail.

### Agent rules

- Keep manifest fields in the Plasmo-supported location already used by the repo.
- Confirm generated Chrome MV3 output before manual load.
- Prefer WXT if content-script UI is not central.

## CRXJS Vite

Use CRXJS when an existing Vite app needs Chrome extension output with minimal restructuring.

### Setup

```bash
npm create vite@latest my-crx-ext -- --template react-ts
cd my-crx-ext
npm install @crxjs/vite-plugin@beta
```

### Core config

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { crx } from "@crxjs/vite-plugin";
import manifest from "./manifest.json";

export default defineConfig({
  plugins: [react(), crx({ manifest })],
});
```

### Important distinction

CRXJS can use source paths inside `manifest.json` as Vite entry points. Chrome still loads only the processed `dist/` output. Validate `dist/manifest.json`, not the source manifest alone.

## Vanilla + Vite

Use vanilla + Vite only when explicit control is more important than framework convenience.

### Required source/output split

```text
public/
  manifest.json
  icons/
  _locales/
src/
  background/index.ts
  content/index.ts
  popup/index.html
  popup/main.ts
  options/index.html
  sidepanel/index.html
vite.config.ts
dist/
  manifest.json
  background/index.js
  content/index.js
  popup/index.html
  icons/
```

### Manifest rule

`public/manifest.json` must reference built output paths such as `background/index.js`, `content/index.js`, and `popup/index.html`. Do not point a hand-written manifest at `src/*.ts`.

### Vite rule

Set Rollup inputs for every HTML and script entry point that Chrome will load. Keep extension TypeScript scoped to the extension package so unrelated workspace type errors do not block the extension build.

## Anti-Selections

| Signal | Avoid |
|---|---|
| "Need one codebase for Chrome, Firefox, Safari" | Do not solve inside this skill |
| "Need Edge enterprise policy deployment" | Do not solve inside this skill |
| "Need browser automation" | Use `run-playwright` or `run-agent-browser` |
| "Need npm package publishing" | Use `publish-npm-package` |
| "Need only a generic React widget" | Use the repo's frontend/app skill |

## Output Checklist

After choosing a framework, final notes should include:

- chosen framework and reason
- output directory loaded in Chrome
- source manifest vs generated manifest distinction
- commands run
- manifest/preflight script results
- any out-of-scope browser targets explicitly deferred
