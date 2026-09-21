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
