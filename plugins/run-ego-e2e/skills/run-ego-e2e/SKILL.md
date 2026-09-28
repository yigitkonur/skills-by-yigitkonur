---
name: run-ego-e2e
description: "Use if running user-faithful agentic end-to-end web tests using ego-browser, testing PR features, verifying live journeys, and parallelizing test runs across Herdr workspaces."
---

# Run Ego E2E — Agentic End-to-End Testing

`run-ego-e2e` drives `ego-browser` to perform user-faithful, agentic end-to-end testing of web applications, live deployments, and merged PR features. It replaces rigid headless test scripts with an adaptive, observable cognitive loop: observe live DOM semantics (`snapshotText`), interact with real UI controls (`click`, `fillInput`, `pressKey`), assert application state via browser evaluation (`js`), and parallelize multi-suite test matrices across isolated Herdr workspaces.

---

## 1. When to Use

### Use This Skill When:
- Verifying merged PRs or deployment candidates end-to-end like a real human user.
- Testing complex multi-route workflows (e.g. login/onboarding, brand selection, dashboard metrics, filter chip sets, billing/Stripe portals).
- Auditing dynamic state changes (theme switching, language localization `t("EN", "TR")`, popovers, modal dialogues).
- Running parallelized browser test suites across multiple Herdr split panes without tab or cookie collisions.

### Do NOT Use This Skill When:
- Running isolated unit or integration tests (use `npm test`, `vitest`, or `jest` directly).
- Running headless API smoke checks without UI (use `curl` or `serverFetch`).
- Performing visual CSS layout/breakpoint audits only (use `audit-ui-and-save-files`).

---

## 2. The 5-Phase E2E Test Lifecycle

Every test journey in `run-ego-e2e` strictly adheres to a 5-phase lifecycle executed via `ego-browser nodejs <<'EOF'` heredocs.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           5-PHASE E2E TEST LIFECYCLE                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Phase 1: Session Isolation  ──► useOrCreateTaskSpace('suite-name')              │
│ Phase 2: Navigation & Wait  ──► openOrReuseTab(url, { wait: true }) + wait(2)  │
│ Phase 3: Semantic Action    ──► snapshotText() ──► click('@N') / fillInput(...) │
│ Phase 4: State Assertion    ──► js(() => ({ ... })) ──► cliLog(JSON.stringify) │
│ Phase 5: Clean Teardown     ──► (Dedicated heredoc) completeTaskSpace(..., false)│
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Task Space Isolation
Always anchor tests in a named, isolated task space. This isolates cookies, local storage, and tabs while inheriting user authentication if needed:
```js
const task = await useOrCreateTaskSpace('e2e-overview-suite')
cliLog('Task Space initialized: ' + task.id)
```

### Phase 2: Navigation & SPA Hydration
Open or reuse a tab and allow client-side hydration to settle:
```js
const tab = await openOrReuseTab('https://zeoradar.endpoints.lol/', { wait: true, timeout: 30 })
await wait(2) // Allow SPA routing and mock/live RPCs to hydrate
```

### Phase 3: Semantic Observation & Interaction
Observe the rendered DOM semantics via `snapshotText()`, then target controls using `@N` refs, CSS selectors, or `xpath=...`:
```js
const snapshot = await snapshotText()
cliLog('Page snapshot:\n' + snapshot.slice(0, 1500))

// Click target using @ref or verified selector
await click('.asset-card:nth-child(2)', { label: 'Select Hepsiburada Brand' })
await wait(2)
```

### Phase 4: State & DOM Assertion
Assert state by evaluating a single self-invoking browser function (`js`), logging results through `cliLog`:
```js
const state = await js(String.raw`(() => {
  return {
    url: window.location.pathname,
    title: document.title,
    visibility: document.querySelector('.metric-card')?.innerText?.trim(),
    hasErrors: !!window.__lastError
  };
})()`)

cliLog('Assertion State: ' + JSON.stringify(state))
if (state.hasErrors) throw new Error('Client error detected during journey');
```

### Phase 5: Dedicated Teardown Round
> [!IMPORTANT]
> `completeTaskSpace(nameOrId, { keep: false })` **must occupy its own dedicated final heredoc** and run only after prior test heredocs have verified completion.
```bash
ego-browser nodejs <<'EOF'
const res = await completeTaskSpace('e2e-overview-suite', { keep: false })
cliLog('Teardown result: ' + JSON.stringify(res))
EOF
```

---

## 3. Dual Execution Modes

### Mode 1: Solo Agent REPL (Sequential Interactive)
Driven by a single agent in the active shell pane. Best for exploratory verification, single PR smoke testing, or step-by-step debugging.
- Runs sequentially from Phase 1 to Phase 5.
- Logs immediate feedback to the console via `cliLog`.

### Mode 2: Herdr Parallel Fleet (Multi-Agent Swarm)
Driven by the Engineering Manager or CTO orchestrator across split panes or dedicated worktree workspaces in Herdr.
- **Decomposition**: Break the test matrix into disjoint suites (e.g. `Suite-Overview`, `Suite-Analytics`, `Suite-Settings`).
- **Parallel Dispatch**: Launch subagents or run commands in separate Herdr panes (`herdr pane split` or `herdr tab create`).
- **Zero Collision Guarantee**: Each worker targets its own unique `useOrCreateTaskSpace('suite-<id>')`. `ego-browser` provisions isolated browsing contexts concurrently on the same host without cross-talk.
- **Aggregation & Pane Retirement**: The manager aggregates worker test reports (`E2E_REPORT: suite=<ID> passed=<N> failed=<M>`), verifies all suites green, and promptly retires worker panes (`herdr pane close <PANE_ID>`).

See [references/herdr-parallel-execution.md](references/herdr-parallel-execution.md) for full parallel fleet orchestration protocols.

---

## 4. Load-Bearing Invariants & Rules

| # | Invariant | Rule |
|---|---|---|
| 1 | **Context Boundary Separation** | Code in the heredoc runs in **Node.js**; code inside `js(...)` runs in the **browser**. Never call `document` or `window` at top-level heredoc scope. |
| 2 | **Single IIFE for `js()`** | Always wrap multi-step browser evaluations in a single self-invoking closure (`String.raw\`(() => { ... })()\``) and return once. Don't chain multiple loose `await js()` calls. |
| 3 | **Output Exclusively via `cliLog`** | Terminal output inside heredocs must use `cliLog(...)`. Standard `console.log` may be swallowed or malformed by the PTY. |
| 4 | **Clean Selector Hygiene** | Element targets accept CSS selectors (`.btn`, `#modal`), `xpath=//...`, `@N` refs from the latest `snapshotText()`, or `text=...`. Never invent unsupported pseudo-selectors like `:has-text(...)` inside raw CSS. |
| 5 | **Dedicated Teardown Round** | Never append `completeTaskSpace` at the end of an active test heredoc. Always run it in a separate, dedicated final heredoc. |
| 6 | **Zero Lingering Task Spaces** | Every test session must conclude with `{ keep: false }` unless manual human inspection was explicitly requested. |
| 7 | **Action Verification vs Silent No-Op Detection** | Never assume `click()` succeeded just because it resolved without error. Headless synthetic clicks can be silently swallowed by `event.stopPropagation()` or `pointer-events: none` on ancestor containers. Always follow actions with an explicit DOM state verification or URL change check. |
| 8 | **Preflight Session Reset for Auth Journeys** | When testing standalone auth/login routes (e.g. `/auth`), pre-existing tokens in `localStorage` or `sessionStorage` can trigger immediate redirect loops to the dashboard. Always invoke storage cleanup before navigating to auth entry points. |
| 9 | **Adaptive Predicate Polling Over Hardcoded Sleep** | Replace brittle, arbitrary `wait(N)` calls with predicate polling (`while (!condition && elapsed < timeout) await wait(0.5)`) inside `js()` to ensure hydration and animations settle without race conditions. |
| 10 | **Landing Route & Inner View Disambiguation** | In modern SPAs, the root path (`/`) frequently mounts a portfolio summary, brand index, or multi-tenant launcher rather than single-entity KPI scorecards. Always inspect initial semantics (`snapshotText()`) before asserting sub-view metrics. If on a portfolio view (`.home`, `.all-assets-toolbar`, `.asset-card`), assert portfolio coverage or navigate into an active entity (`#/slug` or clicking the first entity card) before running entity scorecard assertions. |
| 11 | **Dynamic Auth Gate & Dev Bypass Protocol** | When loading application entrypoints in testing or preview environments, check for login gates, sign-in overlays, or dev bypass controls (`window.zeoBypassLogin()`, `#bypass-btn`, or `text="Bypass login gate"`). Trigger the bypass in Phase 3 before executing feature assertion matrices. |
| 12 | **Client Data Provider & Runtime Parity Assertion** | For applications powered by dual-driver or client-side data providers (e.g. `window.ZEO_DATA_PROVIDER`), assert runtime transport and mode directly (`getMode()`, `getTransport()`) to guarantee execution against expected production or staging backends without silent mock fallbacks. |

---

## 5. Inline Diagnostic Probes & Failure Triage

When an interaction fails or an assertion does not pass, scouts must NOT make blind guesses. Use surgical inline diagnostic probes inside `js(...)`:

1. **Unresponsive Click Diagnosis**: Probe whether the click reached `document`, and trace ancestor elements for inline `stopPropagation()` or `pointer-events: none` blockers (see [references/ego-runtime-cheatsheet.md §6 Trap 1](references/ego-runtime-cheatsheet.md#trap-1-unresponsive-clicks-event-bubbling--stoppropagation)).
2. **URL Hash Sanitization Proof**: When testing OAuth redirects or hash callbacks, inspect `window.location.hash` and `window.location.href` to prove sensitive tokens (`#access_token=...`) are sanitized via `history.replaceState` without leaking into browser history.
3. **Modal & Drawer Escape Dismissal**: Verify both explicit close buttons (`[data-action="close-..."]`) and keyboard `Escape` dismissals work cleanly without leaving orphaned backdrop overlays (`.modal-backdrop`).

---

## Canonical References

| Reference | When to Read | Topics |
|---|---|---|
| [references/test-matrix-and-recipes.md](references/test-matrix-and-recipes.md) | Writing test scripts for standard web application patterns. | Brand selection, metric cards, filter chips, theme toggles, i18n localization, modals, billing portals, OAuth & SAML SSO, sliding drawers. |
| [references/herdr-parallel-execution.md](references/herdr-parallel-execution.md) | Orchestrating multi-agent parallel test fleets via Herdr. | Workspace provisioning, disjoint task space assignment, callback reporting, pane retirement. |
| [references/ego-runtime-cheatsheet.md](references/ego-runtime-cheatsheet.md) | Looking up syntax, flags, and options for ego-browser helpers. | Navigation, observation, mouse/scroll, keyboard, evaluation, task space control API, and 5-point diagnostic playbook. |
