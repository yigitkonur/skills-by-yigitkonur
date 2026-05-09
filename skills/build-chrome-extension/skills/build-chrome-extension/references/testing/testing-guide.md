# Chrome Extension Testing Guide

Keep testing guidance extension-specific: manifest validation, Chrome load checks, service-worker restart resilience, Chrome API mocks, package preflight, and the minimum Playwright/Puppeteer facts needed to launch an extension.

Verified: 2026-05-09 against:

- [Playwright Chrome extensions](https://playwright.dev/docs/chrome-extensions)
- [Chrome extension service worker lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle)
- [Chrome debug extensions tutorial](https://developer.chrome.com/docs/extensions/get-started/tutorial/debug)

Route general browser-driving, broad E2E authoring, screenshots, form automation, and live page workflows to `run-playwright` or `run-agent-browser`.

## Test Layers

| Layer | Scope | Tools |
|---|---|---|
| Static package checks | Built manifest paths, MV3 shape, CSP, icons, locales, junk files | Bundled scripts |
| Unit tests | Pure business logic, URL matching, parsing, message reducers | Vitest/Jest |
| Integration tests | Chrome API wrappers, storage helpers, message dispatchers | Test doubles for `chrome.*` |
| Manual Chrome load | Actual extension install, service worker, popup, content scripts | `chrome://extensions` |
| Extension E2E smoke | Extension loads in Chromium and a popup/content-script path works | Playwright/Puppeteer |

Default split: unit-test logic heavily, integration-test extension glue narrowly, and keep browser E2E as smoke coverage for Chrome-specific behavior.

## Built Output Checks

Run against the directory Chrome will load:

```bash
scripts/check-mv3-manifest.sh dist
scripts/preflight-extension.sh dist
```

Framework output map:

| Framework | Directory |
|---|---|
| WXT dev | `.output/chrome-mv3-dev/` |
| WXT production | `.output/chrome-mv3/` |
| Plasmo dev | `build/chrome-mv3-dev/` |
| Plasmo production | `build/chrome-mv3-prod/` |
| CRXJS / vanilla Vite | `dist/` |

These scripts catch deterministic issues before Chrome is involved:

- missing manifest or invalid JSON
- non-MV3 manifest
- manifest paths pointing at source files
- missing service worker/content script/popup/icon files
- unsafe CSP
- invalid `_locales/*/messages.json`
- junk files in package input

## Unit Tests

Unit-test code that has no Chrome dependency:

- URL and match-pattern helpers
- parsers and formatters
- storage schema migration functions
- message validation and dispatch reducers
- content extraction logic separated from DOM mutation

Keep content scripts thin:

```typescript
export function extractPrice(text: string): number | null {
  const match = text.match(/\$(\d+(?:\.\d{2})?)/);
  return match ? Number(match[1]) : null;
}
```

Test that function normally, then smoke-test real injection in Chrome.

## Chrome API Mocks

Mock only the API surface used by the code under test.

```typescript
import { vi } from "vitest";

const store: Record<string, unknown> = {};

vi.stubGlobal("chrome", {
  runtime: {
    sendMessage: vi.fn(),
    onMessage: { addListener: vi.fn(), removeListener: vi.fn() },
    getURL: vi.fn((path: string) => `chrome-extension://fake/${path}`),
  },
  storage: {
    local: {
      get: vi.fn(async (key?: string) => key ? { [key]: store[key] } : { ...store }),
      set: vi.fn(async (items: Record<string, unknown>) => Object.assign(store, items)),
      remove: vi.fn(async (key: string) => delete store[key]),
    },
    onChanged: { addListener: vi.fn(), removeListener: vi.fn() },
  },
});
```

Do not mock Chrome so broadly that tests pass when the manifest or real context would fail.

## Manual Chrome Load

Use this whenever manifest, permissions, service worker, content scripts, or package output changed:

1. Build the extension.
2. Run both bundled scripts.
3. Open `chrome://extensions`.
4. Enable Developer mode.
5. Load the built output directory.
6. Inspect the extension card for load errors.
7. Open the service worker DevTools from **Inspect views**.
8. Exercise popup, side panel, options, and content-script paths as relevant.
9. Record Chrome version and loaded directory in final notes.

## Service-Worker Restart Resilience

Test the behavior most likely to break in MV3:

- state persists after the service worker idles out
- listeners are registered at top level after a restart
- async message handlers return `true`
- alarms are recreated on install/startup when required
- ports reconnect or fall back to storage-backed state

Chrome normally terminates extension service workers after roughly 30 seconds of inactivity. Do not keep DevTools open during the final restart check because inspecting the service worker keeps it active.

## Playwright Extension Smoke Tests

Current Playwright facts, Verified: 2026-05-09:

- extensions work only in Chromium with a persistent context
- use Playwright's bundled Chromium because Google Chrome and Microsoft Edge removed the sideload flags needed for this workflow
- `channel: "chromium"` allows extension testing in headless mode; headed mode is also valid
- wait for the MV3 service worker and derive the extension ID from its URL

Minimal launch shape:

```typescript
import { chromium } from "@playwright/test";
import path from "node:path";

const extensionPath = path.join(__dirname, "../dist");
const context = await chromium.launchPersistentContext("", {
  channel: "chromium",
  args: [
    `--disable-extensions-except=${extensionPath}`,
    `--load-extension=${extensionPath}`,
  ],
});

let [worker] = context.serviceWorkers();
if (!worker) worker = await context.waitForEvent("serviceworker");
const extensionId = worker.url().split("/")[2];
```

Keep this reference to launch and extension-ID mechanics. For full Playwright suite design, selectors, screenshots, traces, or browser workflows, route to `run-playwright`.

## Package Preflight

Before Web Store packaging:

- production build only
- manifest script passes
- package preflight passes or warnings are documented
- zip root contains `manifest.json`
- zip excludes junk and tests
- permission justifications are ready
- Privacy practices notes are ready

## Output Evidence

Testing reports should include:

- built directory tested
- Chrome version, if manually loaded
- scripts run and pass/fail output
- unit/integration/E2E commands run
- service-worker restart result or not-exercised caveat
- content-script URL coverage
- permissions/runtime grant checks
- zip path when packaged
