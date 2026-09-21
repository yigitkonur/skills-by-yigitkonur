# Ego-Browser Runtime Cheatsheet

This reference provides a concise, high-speed API index for writing `ego-browser nodejs <<'EOF'` heredoc scripts.

---

## 1. Task Space Control API

| Helper | Signature | Description |
|---|---|---|
| `useOrCreateTaskSpace` | `await useOrCreateTaskSpace(nameOrId)` | Connects to or provisions an isolated browsing session. |
| `completeTaskSpace` | `await completeTaskSpace(nameOrId, { keep: false })` | Closes and cleans up the task space (mandatory final round). |
| `listTaskSpaces` | `await listTaskSpaces()` | Lists all active agent and user task spaces. |
| `claimTaskSpace` | `await claimTaskSpace(id)` | Transfers ownership of an existing task space to the agent. |
| `handOffTaskSpace` | `await handOffTaskSpace([nameOrId])` | Hands browser control to human user for captcha/login. |
| `takeOverTaskSpace` | `await takeOverTaskSpace([nameOrId])` | Regains browser control after user confirms continue. |

---

## 2. Navigation & Window State

| Helper | Signature | Description |
|---|---|---|
| `openOrReuseTab` | `await openOrReuseTab(url, { wait: true, timeout: 30 })` | Opens URL in a new or matching tab. |
| `gotoAndWait` | `await gotoAndWait(url, { timeout: 20 })` | Navigates inside the currently selected tab. |
| `pageInfo` | `await pageInfo()` | Returns `{ url, title, w, h, sx, sy, pw, ph }`. |
| `currentTab` | `await currentTab()` | Returns descriptor of current active tab. |
| `listTabs` | `await listTabs()` | Lists all open tabs in current task space. |
| `switchTab` | `await switchTab(targetId)` | Sets active tab by ID. |
| `closeTab` | `await closeTab([targetId])` | Closes specified tab or active tab. |

---

## 3. Observation & Screen Capture

| Helper | Signature | Description |
|---|---|---|
| `snapshotText` | `await snapshotText({ scope: 'full_page' })` | Returns formatted DOM semantic tree with `@N` refs. |
| `captureScreenshot` | `await captureScreenshot()` | Saves visual PNG of the viewport or page. |
| `drainEvents` | `await drainEvents()` | Returns accumulated page events (network, console, etc.). |

---

## 4. Mouse & Input Interactions

| Helper | Signature | Description |
|---|---|---|
| `click` | `await click(target, { label?: string })` | Clicks element center. Target: CSS, `@N`, `xpath=...`, `[x, y]`. |
| `doubleClick` | `await doubleClick(target, { label?: string })` | Double-clicks target. |
| `hover` | `await hover(target, { label?: string })` | Hovers over target to reveal hover menus or tooltips. |
| `dragMouse` | `await dragMouse([from, to], { label?: string })` | Drags mouse from coordinate `from` to `to`. |
| `fillInput` | `await fillInput(target, text)` | Clears input field and types replacement text. |
| `typeText` | `await typeText(text)` | Types raw text into currently focused element. |
| `pressKey` | `await pressKey('Enter' \| 'Escape' \| ...)` | Sends single keydown/keyup sequence. |

---

## 5. Delays & Evaluation

| Helper | Signature | Description |
|---|---|---|
| `wait` | `await wait(seconds)` | Blocks execution for `N` seconds (e.g. `await wait(2)`). |
| `waitForElement` | `await waitForElement(target, { timeout: 10 })` | Blocks until matching element exists in DOM. |
| `waitForNetworkIdle` | `await waitForNetworkIdle({ timeout: 15 })` | Blocks until in-flight requests settle. |
| `js` | `await js(String.raw\`(() => { ... })()\`)` | Evaluates script in page context. Returns evaluated result. |
| `cdp` | `await cdp(method, params)` | Raw Chrome DevTools Protocol command. |
| `cliLog` | `cliLog(message)` | Prints message to terminal output. |

---

## 6. Diagnostic Playbook: Resolving Common E2E Traps

### Trap 1: Unresponsive Clicks (Event Bubbling & StopPropagation)
When clicking an element (`click('...')`) succeeds without throwing errors, but triggers zero UI state change or network dispatch:
```js
const diag = await js(String.raw`(() => {
  const el = document.querySelector('.my-button');
  if (!el) return { error: 'Element not found' };
  
  // 1. Check if click reaches document (delegated listeners)
  let heardAtDoc = false;
  const probe = () => { heardAtDoc = true; };
  document.addEventListener('click', probe, { once: true });
  el.click();
  
  // 2. Check parent containers for stopPropagation or pointer-events: none
  let current = el;
  const blockers = [];
  while (current && current !== document.body) {
    const inlineClick = current.getAttribute('onclick') || '';
    if (inlineClick.includes('stopPropagation')) blockers.push({ tag: current.tagName, class: current.className, blocker: 'onclick-stopPropagation' });
    const pe = window.getComputedStyle(current).pointerEvents;
    if (pe === 'none') blockers.push({ tag: current.tagName, class: current.className, blocker: 'pointer-events: none' });
    current = current.parentElement;
  }
  
  return { heardAtDoc, blockers, outerHTML: el.outerHTML };
})()`)
cliLog('Click Diagnosis: ' + JSON.stringify(diag, null, 2))
```

### Trap 2: Session Boot Gate Redirects (The `/auth` Redirect Trap)
When navigating directly to `/auth` unexpectedly redirects to `/` or the dashboard:
```js
// The SPA boot gate detects an active session in storage and forces a redirect.
// Preflight: Explicitly clear authentication state for auth flow tests:
await js(String.raw`(() => {
  localStorage.removeItem('supabaseAuth');
  localStorage.removeItem('mockAuth');
  sessionStorage.clear();
})()`)
await gotoAndWait('https://zeoradar.endpoints.lol/auth', { timeout: 20 })
```

### Trap 3: URL Token Hash Cleansing Verification
When testing OAuth/SAML token sanitization where `#access_token=...` must be cleansed:
```js
const tokenUrl = 'https://zeoradar.endpoints.lol/auth#access_token=test_jwt&token_type=bearer'
await openOrReuseTab(tokenUrl, { wait: true, timeout: 20 })
await wait(2)

const hashCheck = await js(String.raw`(() => ({
  href: window.location.href,
  hash: window.location.hash,
  hasTokenInHash: window.location.hash.includes('access_token'),
  hasTokenInHref: window.location.href.includes('access_token')
}))()`)
cliLog('Hash Sanitization Proof: ' + JSON.stringify(hashCheck))
if (hashCheck.hasTokenInHref) throw new Error('Token leaked in address bar!');
```

### Trap 4: Stale Asset Caching After Live Deployments (CDP Cache Invalidation)
When verifying freshly deployed releases in `ego-browser`, Chromium may serve cached JavaScript assets (`assets/*.js`) from disk/memory:
```js
// Force Chromium to dump disk/memory cache and reload without cache headers:
await cdp('Network.clearBrowserCache');
await cdp('Page.reload', { ignoreCache: true });
await wait(3);
```

### Trap 5: Adaptive Predicate Polling Over Brittle Sleep
Hardcoded `await wait(N)` can result in flaky test failures when network latency varies or hydration takes longer than usual:
```js
// Resilient predicate polling pattern:
const pollUntilReady = async (selector, timeoutSec = 10) => {
  const start = Date.now();
  while ((Date.now() - start) < timeoutSec * 1000) {
    const ready = await js(String.raw`(() => !!document.querySelector('${selector}'))()`);
    if (ready) return true;
    await wait(0.5);
  }
  throw new Error(`Timeout waiting for selector: ${selector}`);
};
await pollUntilReady('.metric-card');
```

### Trap 6: Modal & Drawer Escape Key Dismissal
When testing modals, dialogs, or sliding drawers, verify that pressing the `Escape` key cleanly closes them without leaving orphaned backdrop overlays:
```js
await pressKey('Escape');
await wait(1);
const isDismissed = await js(String.raw`(() => {
  const modal = document.querySelector('.modal, .drawer, .cite-drawer');
  const backdrop = document.querySelector('.modal-backdrop, .overlay');
  return !modal && !backdrop;
})()`);
if (!isDismissed) throw new Error('Modal failed to close on Escape key');
```

