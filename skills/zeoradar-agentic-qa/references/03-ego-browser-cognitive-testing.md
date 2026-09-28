# 03 — Cognitive Ego-Browser Testing Lifecycle

The hallmark of the `zeoradar-agentic-qa` skill is **cognitive agent testing**. Rigid bash or Node.js test scripts that blindly replay pre-baked DOM clicks are strictly prohibited for test execution logic. Scripts are reserved exclusively for logging, evidence serialization, and SCP file pulling.

An agent running this skill acts as an inquisitive, adversarial human QA engineer.

---

## 1. Why Cognitive Testing Beats Scripted Replays

| Dimension | Scripted Replays (Banned) | Cognitive Ego-Browser (Required) |
|---|---|---|
| **Layout Drift** | Breaks on minor DOM class renames or CSS padding changes. | Adapts dynamically using semantic snapshots (`snapshotText()`), `@N` refs, and flexible text selectors. |
| **Silent Defects** | Passes as long as exit code is 0, even if the UI renders blank tables or `NaN%`. | Inspects rendered visuals, notices missing data, overlapping modals, unlocalized strings, and truncated text. |
| **Edge Case Exploration** | Executes only the happy path encoded in the script. | Challenges boundaries: tries Unicode diacritics, resizes viewports, tests rapid double clicks, observes network errors. |

### The Anti-Injection & Real-User Principle
Never bypass UI flows by calling backend APIs, inserting mock records into databases (e.g. Supabase REST/SQL seeding), or fabricating artificial local storage entries. Every E2E test MUST simulate the authentic actions of an end user on **`https://zeoradar.endpoints.lol/`**:
1. Typing text into real input elements via `fillInput()`.
2. Clicking buttons, toggles, checkboxes, and dropdowns via `click()`.
3. Waiting for asynchronous background workers and network responses to complete naturally.
4. Observing rendered UI state via `snapshotText()` and DOM assertions.
If a feature cannot be created or operated through the UI, it is broken from the user's perspective. Synthetic database seeding is NOT verification.

---

## 2. The 5-Phase Ego-Browser Lifecycle

Every test journey follows a strictly separated 5-phase lifecycle executed via `ssh macbook "ego-browser nodejs << 'EOF' ... EOF"`:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                        5-PHASE EGO BROWSER LIFECYCLE                           │
├────────────────────────────────────────────────────────────────────────────────┤
│ Phase 1: Task Space Isolation  ──► useOrCreateTaskSpace('zeoradar-suite-0X')   │
│ Phase 2: Navigation & Wait     ──► openOrReuseTab(url) + wait(2)               │
│ Phase 3: Semantic Action       ──► snapshotText() ──► click('@N') / fillInput  │
│ Phase 4: State Assertion       ──► js(() => ({ ... })) ──► cliLog(JSON)        │
│ Phase 5: Clean Teardown        ──► (Dedicated heredoc) completeTaskSpace(..., F)│
└────────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Task Space Isolation
Anchor each subagent or test lane in an isolated task space. This isolates cookies, localStorage, and active tabs while allowing inheritance of the baseline session:
```js
const task = await useOrCreateTaskSpace('zeoradar-suite-03-overview');
cliLog('Task Space initialized: ' + task.id);
```

### Phase 2: Navigation & SPA Hydration
Navigate to the target route and allow the single-page application and data providers to settle:
```js
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/overview', { wait: true, timeout: 30 });
await wait(2); // Allow SPA router and provider caches to hydrate
```

### Phase 3: Semantic Observation & Interaction
Always capture a semantic snapshot before clicking or typing. This gives the agent cognitive visibility into the actual DOM tree:
```js
const snapshot = await snapshotText();
cliLog('DOM Snapshot:\n' + snapshot.slice(0, 1500));

// Target controls via verified CSS selector, text, or @ref
await click('.ct-switch[data-action="ov-compare"]', { label: 'Toggle Compare Switch' });
await wait(1);
```

### Phase 4: State & Invariant Assertions
Assert application state by evaluating a single self-invoking function inside the browser context via `js()`. Never guess; extract ground truth from the DOM and runtime:
```js
const assertion = await js(String.raw`(() => {
  const isCompareActive = document.querySelector('.ct-switch[data-action="ov-compare"]')?.classList.contains('on');
  const metricCards = Array.from(document.querySelectorAll('.kpi-card')).map(c => ({
    title: c.querySelector('.kpi-title')?.innerText?.trim(),
    value: c.querySelector('.kpi-value')?.innerText?.trim()
  }));
  const hasErrors = !!window.__lastError || !!document.querySelector('.toast.toast-error');

  return {
    url: window.location.href,
    isCompareActive,
    metricCount: metricCards.length,
    metricCards,
    hasErrors
  };
})()`);

cliLog('State Assertion Result: ' + JSON.stringify(assertion));
if (assertion.hasErrors) throw new Error('Client error detected during comparison toggle');
```

### Phase 5: Dedicated Teardown Heredoc
Teardown must **always occupy its own separate, dedicated final heredoc**. Never mix teardown into assertion heredocs:
```bash
ssh macbook "ego-browser nodejs << 'EOF'
const res = await completeTaskSpace('zeoradar-suite-03-overview', { keep: false });
cliLog('Teardown result: ' + JSON.stringify(res));
EOF"
```

---

## 3. Cognitive Observation Checklist for Agents

During Phase 3 and Phase 4, the agent must actively look for and report:
1. **Raw `null` / `undefined` / `NaN` Leaks**: Values like `NaN%`, `undefined mentions`, or `null` in KPI cards or SVG graphs.
2. **Localization Leaks**: English text showing when Turkish is active, or vice-versa (e.g. untranslated buttons, missing `t()`).
3. **Turkish Character Integrity**: Dotted `İ`/`i` and dotless `I`/`ı` case conversions in search inputs and filters.
4. **Visual Overlaps & Clipping**: Drawer backdrops failing to cover underlying content, modal z-index layering collisions, text overflowing pill containers.
5. **Console & Network Exceptions**: Unhandled promise rejections, 404/500 errors on API endpoints.
6. **In-Flight vs Sealed Measurement States**: Check `.ov-kpi-val-pending` and `.ov-kpi-delta.in-progress` when an initial measurement run is active; verify transition to `Baseline established (1 run)` once sealed.
7. **Empty vs Populated Matrix States**: Assert that prompt rows, citation cells, and category badges match the seeded prompt inventory (see [references/07-edge-cases-and-readiness-gates.md](07-edge-cases-and-readiness-gates.md)).
