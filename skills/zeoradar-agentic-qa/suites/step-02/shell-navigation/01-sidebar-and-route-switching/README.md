# Test Suite 01: Sidebar Navigation, Route Switching & Brand Selector

## 1. Module Overview & Architectural Grounding

The **Global Application Shell Navigation & Route Switching** subsystem (`assets/ui-shell.js`, `assets/router.js`, `assets/radar.js`, `assets/radar.css`) coordinates client-side routing, asset workspace scoping, collapsible sidebar layouts, responsive mobile drawers, and contextual tab dispatching across Zeo Geo-Radar.

### Layout Topology & Component Seams
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                APPLICATION SHELL LAYOUT                                │
├───────────────────────────────┬────────────────────────────────────────────────────────┤
│ SIDEBAR (.sidebar)            │ TOPBAR (.topbar)                                       │
│ ┌───────────────────────────┐ │ [≡] .nav-toggle | [Fav] Brand Name | [Mode Badge]      │
│ │ Brand Switcher (.side-asset) │ [🔍 Cmd+K Palette] | [☼/☾ Theme] | [✨ Zeo AI]         │
│ └───────────────────────────┘ ├────────────────────────────────────────────────────────┤
│ ┌───────────────────────────┐ │ VIEWPORT / MAIN CONTAINER (.main)                      │
│ │ Nav Tabs (.side-item)     │ │                                                        │
│ │  - Overview               │ │                                                        │
│ │  - Visibility (AEI)       │ │                                                        │
│ │  - Prompts                │ │                                                        │
│ │  - Agent Analytics        │ │                                                        │
│ │  - Opportunities          │ │                                                        │
│ │  - Workflows              │ │                                                        │
│ │  - Automations            │ │                                                        │
│ │  - Pages                  │ │                                                        │
│ │  - Dashboards             │ │                                                        │
│ │  - Custom Reports         │ │                                                        │
│ │  - Brand Hub              │ │                                                        │
│ │  - Integrations           │ │                                                        │
│ │  - Skills                 │ │                                                        │
│ │  - Settings               │ │                                                        │
│ └───────────────────────────┘ │                                                        │
│ ┌───────────────────────────┐ │                                                        │
│ │ Footer Controls (.side-foot)│ │                                                        │
│ │ [☾] Theme | [🎁] New       │ │                                                        │
│ │ [TR/EN] Lang | [?] Info   │ │                                                        │
│ │ [◧] Collapse Menu         │ │                                                        │
│ │ Profile (.profile-trigger)│ │                                                        │
│ └───────────────────────────┘ │                                                        │
└───────────────────────────────┴────────────────────────────────────────────────────────┘
```

### Core State Invariants
All shell operations mutate and react to `window.state`:
- `state.route`: Route mode (`"app"`, `"auth"`, `"checkout"`, `"onboarding"`, `"invite"`, `"share"`).
- `state.slug`: Current brand asset slug (e.g. `"[SLUG]"`, `"daikin"`, `"ulker"`, or `null` for Home Index).
- `state.tab`: Active tab identifier (e.g. `"overview"`, `"aei"`, `"volumes"`, `"agentanalytics"`, `"opportunities"`, `"workflows"`, `"agents"`, `"pages"`, `"dashboards"`, `"reports"`, `"kb"`, `"integrations"`, `"skills"`, `"settings"`, `"account"`).
- `state.sideCollapsed`: Boolean flag indicating if desktop sidebar is minimized.
- `state.openPop`: String key of currently active dropdown or popover (`null` when closed).
- `document.body.classList`:
  - `.side-collapsed`: Desktop sidebar collapsed state (`display: none`).
  - `.side-open`: Mobile drawer slide-in state (`display: flex`).

---

## 2. Directory Structure & Test Cases

This directory contains 10 focused, modular Gherkin QA test cases:

| File Name | Case ID | Title / Purpose | Original Coverage |
|:---|:---|:---|:---|
| `01-gherkin-case-default-route-and-workspace-mount.md` | TC-NAV-01 | Default Route, Workspace Resolution & Active Overview State | E2E-NAV-01 |
| `02-gherkin-case-tab-switcher-cycle-all-tabs.md` | TC-NAV-02 | Full 15-Tab Route Navigation, Subview Cleanup & URL Synchronization | E2E-NAV-02 |
| `03-gherkin-case-brand-switcher-popover-and-selection.md` | TC-NAV-03 | Brand Switcher Popover Lifecycle, Filtering & Workspace Transition | E2E-NAV-03 |
| `04-gherkin-case-desktop-sidebar-collapse-and-expand.md` | TC-NAV-04 | Desktop Sidebar Collapse, Mini-State & Floating Reopen Button | E2E-NAV-04 |
| `05-gherkin-case-mobile-drawer-responsive-lifecycle.md` | TC-NAV-05 | Responsive Mobile Drawer Toggle, Overlay Backdrop & Auto-Dismiss | E2E-NAV-05 |
| `06-gherkin-case-browser-history-popstate-synchronization.md` | TC-NAV-06 | Browser History API (Back/Forward), Popstate Handling & State Restoration | E2E-NAV-06 |
| `07-gherkin-case-invalid-tab-alias-recovery-and-fallback.md` | TC-NAV-07 | Deep-Linking Fallback for Invalid Tab Aliases & Hash Fallback | E2E-NAV-07 |
| `08-gherkin-case-rapid-tab-click-race-concurrency.md` | TC-NAV-08 | Rapid Tab Switching Concurrency, `bootSeq` Monotonic Guard & State Cleanup | E2E-NAV-08 |
| `09-gherkin-case-brand-search-turkish-and-zero-results.md` | TC-NAV-09 | Brand Switcher Adversarial Search, Turkish Case-Folding & Empty State Retention | E2E-NAV-09 |
| `10-gherkin-case-active-brand-reselection-filter-reset.md` | TC-NAV-10 | Active Brand Re-Selection, Filter State Cleansing & Silent URL Invariance | E2E-NAV-10 |

---

## 3. Parameter Vocabulary & Test Placeholders

Test scenarios in this suite use standardized, bracketed placeholders:

| Placeholder | Meaning & System Mapping | Where & How to Set | Representative Test Variants |
|:---|:---|:---|:---|
| `[APP_URL]` | Base origin URL of the running web application | Base URL parameter in `openOrReuseTab` | `https://zeoradar.endpoints.lol` |
| `[DOMAIN]` | Monitored target brand domain under test | Target brand website | `daikin.com.tr` |
| `[COUNTRY]` | ISO 3166-1 alpha-2 country code targeting locale evaluation | Selected country dropdown or detected domain ccTLD | `US`, `TR`, `UK`, `DE`, `FR` |
| `[LANGUAGE]` | IETF language tag for UI localization | App shell language toggle or `state.lang` | `en` (English), `tr` (Turkish) |
| `[ROUTE_TAB]` | Active tab key or path segment identifier | Target in `.side-item[data-key]` or URL `/:slug/:tab` | `overview`, `aei`, `volumes`, `agentanalytics`, `opportunities`, `workflows`, `agents`, `pages`, `dashboards`, `reports`, `kb`, `integrations`, `skills`, `settings`, `account` |
| `[VIEWPORT_SIZE]` | Browser viewport dimensions for responsive layout | Set via browser automation emulation | Desktop (`1440x900`), Tablet (`820x1180`), Mobile (`390x844`) |
| `[SLUG]` | Unique brand identifier in multi-brand catalog | URL path segment `/:slug` or `data-slug` | `daikin`, `ulker`, `superfresh` |
| `[SEARCH_QUERY]` | Filter text entered into search input fields | Input element `.asset-pop .search input` | `ulker`, `ülker`, `ÜLKER`, `nonexistent999xyz`, `super` |

---

## 4. Ego Browser / MacBook Execution Model

### Physical Topology & Gateway
E2E testing is executed using `ego-browser nodejs` on the physical MacBook gateway connected via SSH.

```
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│     Linux Host (Development)     │           │      MacBook Gateway (Live)     │
│                                 │   SSH     │                                 │
│  - Test Suite & Gherkin Specs   │──────────►│  - Ego Browser Runtime (Node)   │
│  - Storage / Result Directories │           │  - Active Display / GPU Render  │
│  - SCP Evidence Downloader      │◄──────────│  - Local Screenshot Cache       │
└─────────────────────────────────┘    SCP    └─────────────────────────────────┘
```

### Execution Lifecycle Protocol
1. **Heredoc Dispatch**: The test script is executed remotely via:
   ```bash
   ssh macbook "ego-browser nodejs <<'EOF'
     const task = await useOrCreateTaskSpace('e2e-shell-nav-suite');
     const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/overview', { wait: true });
     // ... execute semantic actions & assertions
     await completeTaskSpace('e2e-shell-nav-suite', { keep: false });
   EOF"
   ```
2. **MacBook Screenshot Capture**: Screenshots are captured directly on the MacBook display to `/tmp/ego-shots/nav/` or `~/Desktop/shots/`.
3. **Evidence Download via SCP**: Upon scenario completion, the test runner downloads screenshots and network captures to the designated result directory:
   ```bash
   scp macbook:/tmp/ego-shots/nav/case-01-*.png ./01-gherkin-result-case-default-route-and-workspace-mount/screenshots/
   ```
4. **Result Directory Specification**:
   - Each Gherkin case corresponds to an execution result directory named `0X-gherkin-result-case-<slug>/`.
   - Result directories are **NEVER created as empty placeholders**. They are instantiated only by the test execution runner upon executing the suite.
   - A complete result directory contains:
     - `result.md` (Execution outcome, timing, environment specs, pass/fail status)
     - `evidence.json` (Structured DOM dumps, console errors, state snapshots)
     - `screenshots/*.png` (Visual evidence downloaded from MacBook)
     - `network/*.json` (Recorded HTTP / RPC telemetry)

---

## 5. Traceability & Code Coverage Matrix

| Original Scenario ID | Original Title | New Modular Gherkin Case | Real Code Reference & Invariant Hardening |
|:---|:---|:---|:---|
| E2E-NAV-01 | Default Route & Workspace Mounting | `01-gherkin-case-default-route-and-workspace-mount.md` | `assets/router.js:10-18`, `assets/radar.js:4900-4960` (Default slug & tab resolution) |
| E2E-NAV-02 | Tab Switcher Cycle (All 15 Tabs) | `02-gherkin-case-tab-switcher-cycle-all-tabs.md` | `assets/radar.js:5120-5180` (Sidebar click handler, subview cleanup, navigation push) |
| E2E-NAV-03 | Brand Switcher Popover & Live Filter | `03-gherkin-case-brand-switcher-popover-and-selection.md` | `assets/radar.js:5220-5270` (`assetPopHTML`, input filter, `data-slug` navigation) |
| E2E-NAV-04 | Desktop Sidebar Collapse & Expand | `04-gherkin-case-desktop-sidebar-collapse-and-expand.md` | `assets/radar.js:5215-5225` (`state.sideCollapsed`, `body.side-collapsed`, `.side-reopen`) |
| E2E-NAV-05 | Mobile Drawer Open & Auto-Dismiss | `05-gherkin-case-mobile-drawer-responsive-lifecycle.md` | `assets/radar.js:5210-5215` (`side-toggle`, `body.side-open`, auto-remove on click) |
| E2E-NAV-06 | Browser History (Back / Forward) | `06-gherkin-case-browser-history-popstate-synchronization.md` | `assets/router.js:250-295` (`window.addEventListener("popstate")`, history pushState) |
| E2E-NAV-07 | Deep-Linking to Invalid Tab & Hash Fallback | `07-gherkin-case-invalid-tab-alias-recovery-and-fallback.md` | `assets/radar.js:4950-4960` (`else` fallback `sideKey = "aei"`), `assets/router.js:65-80` |
| E2E-NAV-08 | Rapid Tab Switch Concurrency & Stale Lock | `08-gherkin-case-rapid-tab-click-race-concurrency.md` | `assets/radar.js:4850-4880` (`bootSeq` monotonic lock, modalHolder flush, subview reset) |
| E2E-NAV-09 | Brand Switcher Negative Queries & Backdrop | `09-gherkin-case-brand-search-turkish-and-zero-results.md` | `assets/radar.js:5230-5245` (`row.textContent.toLowerCase()`, Turkish `Ü/ü` Unicode folding) |
| E2E-NAV-10 | Re-Selecting Active Brand (Filter Reset) | `10-gherkin-case-active-brand-reselection-filter-reset.md` | `assets/radar.js:5255-5270` (`state.topics = null`, `state.platforms = null`, `silent: true`) |
