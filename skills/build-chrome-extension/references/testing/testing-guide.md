# Chrome Extension Testing Guide (Manifest V3)

## Testing Strategy Overview

| Layer | What It Tests | Tools | Speed | Reliability |
|-------|--------------|-------|-------|-------------|
| Unit | Pure logic, utilities, storage helpers, message parsing | Vitest, Jest | ~1ms/test | High |
| Integration | Chrome API interactions, message passing between contexts | Vitest + chrome-mock, Puppeteer | ~100ms/test | Medium |
| E2E | Full extension in real browser, popup clicks, content script injection | Playwright, Puppeteer | ~2-5s/test | Lower (flaky) |
| Visual Regression | Popup/options UI appearance | Playwright screenshots, Percy | ~3s/test | Medium |

**Recommended split:** 70% unit, 20% integration, 10% E2E.

---

## Unit Testing with Vitest

### Setup

```bash
npm install -D vitest @vitest/coverage-v8 jsdom
```

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "jsdom",
    include: ["src/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      exclude: ["src/**/*.test.ts", "src/types/**"],
    },
    setupFiles: ["./test/setup.ts"],
  },
});
```

### Testing Business Logic

```typescript
// src/utils/url-matcher.ts
export function matchesPattern(url: string, pattern: string): boolean {
  const regex = new RegExp(
    "^" + pattern.replace(/\*/g, ".*").replace(/\?/g, ".") + "$"
  );
  return regex.test(url);
}

export function extractDomain(url: string): string | null {
  try {
    return new URL(url).hostname;
  } catch {
    return null;
  }
}

// src/utils/url-matcher.test.ts
import { describe, it, expect } from "vitest";
import { matchesPattern, extractDomain } from "./url-matcher";

describe("matchesPattern", () => {
  it("matches exact URLs", () => {
    expect(matchesPattern("https://example.com", "https://example.com")).toBe(true);
  });

  it("matches wildcard patterns", () => {
    expect(matchesPattern("https://example.com/page", "https://example.com/*")).toBe(true);
  });

  it("rejects non-matching URLs", () => {
    expect(matchesPattern("https://other.com", "https://example.com/*")).toBe(false);
  });
});

describe("extractDomain", () => {
  it("extracts hostname from valid URL", () => {
    expect(extractDomain("https://sub.example.com/path")).toBe("sub.example.com");
  });

  it("returns null for invalid URL", () => {
    expect(extractDomain("not-a-url")).toBeNull();
  });
});
```

### Testing Storage Helpers

```typescript
// src/storage/settings.ts
export interface Settings {
  enabled: boolean;
  blocklist: string[];
  theme: "light" | "dark";
}

const DEFAULTS: Settings = { enabled: true, blocklist: [], theme: "light" };

export async function getSettings(): Promise<Settings> {
  const result = await chrome.storage.sync.get("settings");
  return { ...DEFAULTS, ...result.settings };
}

export async function updateSettings(partial: Partial<Settings>): Promise<Settings> {
  const current = await getSettings();
  const updated = { ...current, ...partial };
  await chrome.storage.sync.set({ settings: updated });
  return updated;
}

// src/storage/settings.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { getSettings, updateSettings } from "./settings";

// Mock chrome.storage before import
const storageStore: Record<string, unknown> = {};

const chromeMock = {
  storage: {
    sync: {
      get: vi.fn(async (key: string) => {
        return { [key]: storageStore[key] };
      }),
      set: vi.fn(async (items: Record<string, unknown>) => {
        Object.assign(storageStore, items);
      }),
    },
  },
};

vi.stubGlobal("chrome", chromeMock);

beforeEach(() => {
  Object.keys(storageStore).forEach((k) => delete storageStore[k]);
  vi.clearAllMocks();
});

describe("getSettings", () => {
  it("returns defaults when storage is empty", async () => {
    const settings = await getSettings();
    expect(settings).toEqual({ enabled: true, blocklist: [], theme: "light" });
  });

  it("merges stored values with defaults", async () => {
    storageStore.settings = { theme: "dark" };
    const settings = await getSettings();
    expect(settings.theme).toBe("dark");
    expect(settings.enabled).toBe(true); // default preserved
  });
});

describe("updateSettings", () => {
  it("persists partial updates", async () => {
    await updateSettings({ enabled: false });
    expect(chromeMock.storage.sync.set).toHaveBeenCalledWith({
      settings: { enabled: false, blocklist: [], theme: "light" },
    });
  });
});
```

### Testing Message Handlers

```typescript
// src/messages/handler.ts
export type Message =
  | { type: "GET_COUNT" }
  | { type: "INCREMENT"; payload: number }
  | { type: "RESET" };

export function handleMessage(
  message: Message,
  state: { count: number }
): { count: number; response: unknown } {
  switch (message.type) {
    case "GET_COUNT":
      return { count: state.count, response: { count: state.count } };
    case "INCREMENT":
      const newCount = state.count + message.payload;
      return { count: newCount, response: { count: newCount } };
    case "RESET":
      return { count: 0, response: { count: 0 } };
  }
}

// src/messages/handler.test.ts
import { describe, it, expect } from "vitest";
import { handleMessage } from "./handler";

describe("handleMessage", () => {
  it("returns current count for GET_COUNT", () => {
    const result = handleMessage({ type: "GET_COUNT" }, { count: 5 });
    expect(result.response).toEqual({ count: 5 });
  });

  it("increments count", () => {
    const result = handleMessage({ type: "INCREMENT", payload: 3 }, { count: 5 });
    expect(result.count).toBe(8);
  });

  it("resets count to zero", () => {
    const result = handleMessage({ type: "RESET" }, { count: 42 });
    expect(result.count).toBe(0);
  });
});
```

---

## Mocking Chrome APIs

### Manual Mock Setup (Recommended)

```typescript
// test/setup.ts — loaded by vitest setupFiles
import { vi } from "vitest";

const chrome = {
  runtime: {
    sendMessage: vi.fn(),
    onMessage: { addListener: vi.fn(), removeListener: vi.fn(), hasListener: vi.fn() },
    onInstalled: { addListener: vi.fn() },
    getURL: vi.fn((path: string) => `chrome-extension://fake-id/${path}`),
    id: "fake-extension-id",
    lastError: null as chrome.runtime.LastError | null,
  },
  storage: {
    local: { get: vi.fn(), set: vi.fn(), remove: vi.fn(), clear: vi.fn() },
    sync: { get: vi.fn(), set: vi.fn(), remove: vi.fn(), clear: vi.fn() },
    onChanged: { addListener: vi.fn(), removeListener: vi.fn() },
  },
  tabs: {
    query: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    sendMessage: vi.fn(),
    onUpdated: { addListener: vi.fn() },
    onRemoved: { addListener: vi.fn() },
  },
  action: {
    setBadgeText: vi.fn(),
    setBadgeBackgroundColor: vi.fn(),
    setIcon: vi.fn(),
    onClicked: { addListener: vi.fn() },
  },
  alarms: {
    create: vi.fn(),
    clear: vi.fn(),
    onAlarm: { addListener: vi.fn() },
  },
  notifications: {
    create: vi.fn(),
    clear: vi.fn(),
    onClicked: { addListener: vi.fn() },
  },
  contextMenus: {
    create: vi.fn(),
    removeAll: vi.fn(),
    onClicked: { addListener: vi.fn() },
  },
};

vi.stubGlobal("chrome", chrome);
```

### Using `@types/chrome` for Type-Safe Mocks

```typescript
// test/helpers/mock-storage.ts
import { vi } from "vitest";

export function createMockStorage(initial: Record<string, unknown> = {}) {
  const store = { ...initial };

  return {
    get: vi.fn(async (keys?: string | string[] | null) => {
      if (!keys) return { ...store };
      const keyList = typeof keys === "string" ? [keys] : keys;
      const result: Record<string, unknown> = {};
      keyList.forEach((k) => {
        if (k in store) result[k] = store[k];
      });
      return result;
    }),
    set: vi.fn(async (items: Record<string, unknown>) => {
      Object.assign(store, items);
    }),
    remove: vi.fn(async (keys: string | string[]) => {
      const keyList = typeof keys === "string" ? [keys] : keys;
      keyList.forEach((k) => delete store[k]);
    }),
    clear: vi.fn(async () => {
      Object.keys(store).forEach((k) => delete store[k]);
    }),
    _store: store, // for assertions
  };
}
```

---

## Integration Testing with Puppeteer

Use the built manifest to derive the popup path in browser tests. WXT often emits `popup.html`; vanilla/CRXJS builds often emit `popup/index.html`.

```bash
npm install -D puppeteer
```

```typescript
// test/integration/extension.test.ts
import puppeteer, { Browser } from "puppeteer";
import { readFileSync } from "fs";
import path from "path";
import { describe, it, expect, beforeAll, afterAll } from "vitest";

const EXTENSION_PATH = path.resolve(__dirname, "../../dist");
const MANIFEST = JSON.parse(
  readFileSync(path.join(EXTENSION_PATH, "manifest.json"), "utf-8")
);
const POPUP_PATH = MANIFEST.action?.default_popup ?? "popup.html";

let browser: Browser;

beforeAll(async () => {
  browser = await puppeteer.launch({
    headless: "new", // use "new" headless; extensions work in headless=new since Chrome 109
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
      "--no-sandbox",
    ],
  });
});

afterAll(async () => {
  await browser.close();
});

async function getExtensionId(): Promise<string> {
  const targets = browser.targets();
  const sw = targets.find(
    (t) => t.type() === "service_worker" && t.url().includes("chrome-extension://")
  );
  if (!sw) throw new Error("Service worker target not found");
  const match = sw.url().match(/chrome-extension:\/\/([^/]+)/);
  return match![1];
}

describe("Extension popup", () => {
  it("loads and displays title", async () => {
    const extId = await getExtensionId();
    const page = await browser.newPage();
    await page.goto(`chrome-extension://${extId}/${POPUP_PATH}`);
    const title = await page.$eval("h1", (el) => el.textContent);
    expect(title).toBe("My Extension");
    await page.close();
  });

  it("toggle switch persists state", async () => {
    const extId = await getExtensionId();
    const page = await browser.newPage();
    await page.goto(`chrome-extension://${extId}/${POPUP_PATH}`);
    await page.click("#enable-toggle");
    // Reopen popup
    await page.reload();
    const isChecked = await page.$eval("#enable-toggle", (el: HTMLInputElement) => el.checked);
    expect(isChecked).toBe(true);
    await page.close();
  });
});
```

---

## E2E Testing with Playwright

```bash
npm install -D @playwright/test
```

```typescript
// test/e2e/extension.spec.ts
import { test, expect, chromium, BrowserContext } from "@playwright/test";
import { readFileSync } from "fs";
import path from "path";

const EXTENSION_PATH = path.resolve(__dirname, "../../dist");
const MANIFEST = JSON.parse(
  readFileSync(path.join(EXTENSION_PATH, "manifest.json"), "utf-8")
);
const POPUP_PATH = MANIFEST.action?.default_popup ?? "popup.html";

let context: BrowserContext;

test.beforeAll(async () => {
  context = await chromium.launchPersistentContext("", {
    headless: false, // Extensions require headed mode in Playwright
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
    ],
  });
});

test.afterAll(async () => {
  await context.close();
});

function getExtensionId(): string {
  const sw = context.serviceWorkers().find((w) =>
    w.url().includes("chrome-extension://")
  );
  if (!sw) throw new Error("No extension service worker found");
  return sw.url().match(/chrome-extension:\/\/([^/]+)/)![1];
}

test("popup renders correctly", async () => {
  // Wait for service worker to register
  if (context.serviceWorkers().length === 0) {
    await context.waitForEvent("serviceworker");
  }
  const extId = getExtensionId();
  const page = await context.newPage();
  await page.goto(`chrome-extension://${extId}/${POPUP_PATH}`);
  await expect(page.locator("h1")).toHaveText("My Extension");
  await page.close();
});

test("content script injects badge on target page", async () => {
  const page = await context.newPage();
  await page.goto("https://example.com");
  // Wait for content script to inject its element
  const badge = page.locator("#my-extension-badge");
  await expect(badge).toBeVisible({ timeout: 5000 });
  await page.close();
});
```

---

## Testing Content Scripts

| Approach | Pros | Cons |
|----------|------|------|
| JSDOM unit test | Fast, no browser | No real DOM APIs, no `chrome.*`, layout missing |
| Puppeteer/Playwright | Real browser, real injection | Slow, needs running extension build |
| Isolated DOM test | Middle ground | Must mock `chrome.*` and page context |

**Recommended pattern:** extract logic from DOM manipulation, unit-test the logic, E2E-test the injection.

```typescript
// src/content/extractor.ts — pure logic, easily testable
export function extractPriceFromText(text: string): number | null {
  const match = text.match(/\$(\d+(?:\.\d{2})?)/);
  return match ? parseFloat(match[1]) : null;
}

// src/content/content-script.ts — thin DOM layer
import { extractPriceFromText } from "./extractor";

const priceEl = document.querySelector(".product-price");
if (priceEl) {
  const price = extractPriceFromText(priceEl.textContent ?? "");
  if (price !== null) {
    chrome.runtime.sendMessage({ type: "PRICE_FOUND", payload: price });
  }
}
```

---

## Testing Service Worker Restart Resilience

Service workers can terminate at any time. Test that your extension survives restarts.

```typescript
// test/e2e/sw-resilience.spec.ts
import { test, expect, chromium, BrowserContext } from "@playwright/test";
import { readFileSync } from "fs";
import path from "path";

const EXT_PATH = path.resolve(__dirname, "../../dist");
const MANIFEST = JSON.parse(
  readFileSync(path.join(EXT_PATH, "manifest.json"), "utf-8")
);
const POPUP_PATH = MANIFEST.action?.default_popup ?? "popup.html";

test("state persists across service worker restarts", async () => {
  const context = await chromium.launchPersistentContext("", {
    headless: false,
    args: [
      `--disable-extensions-except=${EXT_PATH}`,
      `--load-extension=${EXT_PATH}`,
    ],
  });

  // Wait for SW
  if (context.serviceWorkers().length === 0) {
    await context.waitForEvent("serviceworker");
  }

  const sw = context.serviceWorkers()[0];
  const extId = sw.url().match(/chrome-extension:\/\/([^/]+)/)![1];

  // Set some state via popup
  const popup = await context.newPage();
  await popup.goto(`chrome-extension://${extId}/${POPUP_PATH}`);
  await popup.click("#increment-btn");
  await popup.close();

  // Force-terminate the service worker by navigating to chrome://extensions
  // and then triggering a new event that restarts it
  const page = await context.newPage();
  await page.goto("https://example.com");
  // The content script or alarm will restart the SW

  // Wait for new SW to register
  await context.waitForEvent("serviceworker");

  // Verify state survived
  const popup2 = await context.newPage();
  await popup2.goto(`chrome-extension://${extId}/${POPUP_PATH}`);
  const count = await popup2.$eval("#count", (el) => el.textContent);
  expect(count).toBe("1");

  await context.close();
});
```

---

## CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Test Chrome Extension

on:
  push:
    branches: [main]
  pull_request:

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run test:unit -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run build
      - run: npx playwright install chromium
      - run: xvfb-run npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: e2e-screenshots
          path: test-results/

  lint-and-type:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  package:
    needs: [unit, e2e, lint-and-type]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run build
      - run: cd dist && zip -r ../extension.zip .
      - uses: actions/upload-artifact@v4
        with:
          name: extension-zip
          path: extension.zip
```

### package.json Scripts

```json
{
  "scripts": {
    "test:unit": "vitest run",
    "test:unit:watch": "vitest",
    "test:e2e": "playwright test",
    "test:coverage": "vitest run --coverage",
    "typecheck": "tsc --noEmit",
    "lint": "eslint src/"
  }
}
```

---

## Code Coverage for Extensions

| Area | Target | Notes |
|------|--------|-------|
| Business logic (utils) | 90%+ | Pure functions, easy to test |
| Storage helpers | 80%+ | Mock chrome.storage |
| Message handlers | 80%+ | Extract handler logic from listener |
| Content script logic | 70%+ | Separate DOM from logic |
| Popup/options UI | 60%+ | Component tests for React/Vue/Svelte |
| Service worker glue | 50%+ | Mostly tested via E2E |

```typescript
// vitest.config.ts — coverage thresholds
export default defineConfig({
  test: {
    coverage: {
      provider: "v8",
      thresholds: {
        statements: 75,
        branches: 70,
        functions: 75,
        lines: 75,
      },
    },
  },
});
```

---

## Visual Regression Testing for Popup/Options UI

```typescript
// test/visual/popup.spec.ts
import { test, expect, chromium } from "@playwright/test";
import { readFileSync } from "fs";
import path from "path";

const EXT_PATH = path.resolve(__dirname, "../../dist");
const MANIFEST = JSON.parse(
  readFileSync(path.join(EXT_PATH, "manifest.json"), "utf-8")
);
const POPUP_PATH = MANIFEST.action?.default_popup ?? "popup.html";

test("popup visual snapshot - light theme", async () => {
  const context = await chromium.launchPersistentContext("", {
    headless: false,
    args: [
      `--disable-extensions-except=${EXT_PATH}`,
      `--load-extension=${EXT_PATH}`,
    ],
  });

  if (context.serviceWorkers().length === 0) {
    await context.waitForEvent("serviceworker");
  }

  const sw = context.serviceWorkers()[0];
  const extId = sw.url().match(/chrome-extension:\/\/([^/]+)/)![1];
  const page = await context.newPage();
  await page.setViewportSize({ width: 400, height: 600 });
  await page.goto(`chrome-extension://${extId}/${POPUP_PATH}`);
  await page.waitForLoadState("networkidle");

  await expect(page).toHaveScreenshot("popup-light.png", {
    maxDiffPixelRatio: 0.01,
  });

  await context.close();
});
```

### Playwright Screenshot Config

```typescript
// playwright.config.ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.01,
      animations: "disabled",
    },
  },
  snapshotPathTemplate: "{testDir}/__screenshots__/{testFilePath}/{arg}{ext}",
});
```
