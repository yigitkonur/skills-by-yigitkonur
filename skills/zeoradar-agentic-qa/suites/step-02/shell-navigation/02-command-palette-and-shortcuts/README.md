# Test Suite 02: Command Palette (⌘K) & Global Keyboard Shortcuts

## 1. Module Overview & Architectural Grounding

The **Command Palette (⌘K) & Keyboard Shortcuts** subsystem (`assets/radar.js` lines 6188–6560, `assets/radar.css`, `assets/ui-shell.js`) serves as the global dispatch hub for instant search, workspace navigation, preferences configuration, and keyboard accessibility across Zeo Geo-Radar.

### Modal Architecture & Component Seams
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          COMMAND PALETTE MODAL ARCHITECTURE                            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ #cmdPaletteHolder                                                                      │
│  └─ #cmdPaletteModal.cmd-backdrop [data-action="close-cmd-palette"]                    │
│      └─ .cmd-modal (stopPropagation)                                                   │
│          ├─ .cmd-header                                                                │
│          │   ├─ [🔍] icon("search", 18)                                                │
│          │   ├─ #cmdPaletteInput.cmd-input (autofocus, autocomplete="off")             │
│          │   └─ <kbd class="cmd-kbd">ESC</kbd>                                         │
│          └─ .cmd-body                                                                  │
│              ├─ .cmd-group-title (Category Header)                                     │
│              ├─ .cmd-item.selected [data-action="select-cmd-item"] [data-idx="0"]      │
│              │   ├─ .cmd-item-left: [Icon] + Title                                     │
│              │   └─ .cmd-item-cat: Category Label                                      │
│              ├─ .cmd-item [data-action="select-cmd-item"] [data-idx="1"]                │
│              └─ ... or .cmd-empty ("No results found.")                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Core State Invariants
Command palette operations mutate and react to `window.state.commandPalette`:
```js
state.commandPalette = {
  isOpen: false,               // Boolean modal visibility flag
  query: "",                   // Active search filter string
  selectedIndex: 0,            // Currently highlighted item index (0-based)
  previousActiveElement: null  // DOM node focused prior to palette opening
};
```

---

## 2. Directory Structure & Test Cases

This directory contains 10 focused, modular Gherkin QA test cases:

| File Name | Case ID | Title / Purpose | Original Coverage |
|:---|:---|:---|:---|
| `01-gherkin-case-palette-trigger-keyboard-and-topbar.md` | TC-CMD-01 | Palette Trigger via Keyboard Shortcuts (⌘K / Ctrl+K) and Topbar Button | E2E-CMD-01, E2E-CMD-02 |
| `02-gherkin-case-query-search-and-filtering.md` | TC-CMD-02 | Real-time Query Filtering across Titles and Categories with Caret Preservation | E2E-CMD-03 |
| `03-gherkin-case-arrow-traversal-and-wraparound.md` | TC-CMD-03 | Arrow Key Cycling (Up/Down), Selection Wrapping and Viewport Scrolling | E2E-CMD-04, E2E-CMD-12 |
| `04-gherkin-case-command-execution-enter-and-click.md` | TC-CMD-04 | Command Execution via Enter Key and Direct Mouse Click Dispatch | E2E-CMD-05, E2E-CMD-06 |
| `05-gherkin-case-palette-dismissal-and-focus-recovery.md` | TC-CMD-05 | Palette Dismissal via Escape & Backdrop with Two-Tier Focus Recovery | E2E-CMD-07 |
| `06-gherkin-case-keyboard-accessibility-bridge.md` | TC-CMD-06 | Global WCAG Keyboard Accessibility Bridge for Enter and Spacebar Activation | E2E-CMD-08 |
| `07-gherkin-case-regex-metacharacter-query-immunity.md` | TC-CMD-07 | Adversarial Regex Metacharacters and Syntax Crash Immunity | E2E-CMD-09 |
| `08-gherkin-case-empty-state-and-enter-guard.md` | TC-CMD-08 | Localized Zero-Result Empty State and Safe Enter Key Guard | E2E-CMD-10 |
| `09-gherkin-case-modal-stacking-and-z-index-layering.md` | TC-CMD-09 | Layered Modal Stacking over Active Dialogs and Focus Preservation | E2E-CMD-11 |
| `10-gherkin-case-mobile-viewport-suppression.md` | TC-CMD-10 | Mobile Breakpoint Topbar Trigger Suppression and External Keyboard Accessibility | Responsiveness |

---

## 3. Parameter Vocabulary & Test Placeholders

Test scenarios in this suite use standardized, bracketed placeholders:

| Placeholder | Meaning & System Mapping | Where & How to Set | Representative Test Variants |
|:---|:---|:---|:---|
| `[APP_URL]` | Base origin URL of the running web application | Base URL parameter in `openOrReuseTab` | `https://zeoradar.endpoints.lol` |
| `[DOMAIN]` | Monitored target brand domain under test | Target brand website | `daikin.com.tr` |
| `[COUNTRY]` | ISO 3166-1 alpha-2 country code targeting locale evaluation | Selected country dropdown or detected domain ccTLD | `US`, `TR`, `UK` |
| `[LANGUAGE]` | IETF language tag for UI localization | App shell language toggle or `state.lang` | `en` (English), `tr` (Turkish) |
| `[KEYBOARD_SHORTCUT]` | Key combination to invoke actions | Keydown event (`Meta+K`, `Ctrl+K`, `Escape`, `Enter`) | `⌘K`, `Ctrl+K`, `Escape`, `Enter`, `Space` |
| `[SEARCH_QUERY]` | Filter query string entered into command palette | Input `#cmdPaletteInput` | `theme`, `opportunities`, `[SLUG]`, `[[*+?^${}()|\/]]` |
| `[CATEGORY_NAME]` | Category classification of command items | Field `it.category` | `Workspaces`, `Analytics`, `Action`, `Context`, `Preferences` |
| `[COMMAND_TITLE]` | User-facing command item title | Element `.cmd-item-left span` | `Overview Dashboard`, `Theme: Switch to Dark` |
| `[VIEWPORT_SIZE]` | Viewport size for responsive testing | Emulation viewport | Desktop (`1440x900`), Mobile (`390x844`) |

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
     const task = await useOrCreateTaskSpace('e2e-cmd-palette-suite');
     const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/overview', { wait: true });
     // ... execute semantic actions & assertions
     await completeTaskSpace('e2e-cmd-palette-suite', { keep: false });
   EOF"
   ```
2. **MacBook Screenshot Capture**: Screenshots are captured directly on the MacBook display to `/tmp/ego-shots/cmd/` or `~/Desktop/shots/`.
3. **Evidence Download via SCP**: Upon scenario completion, the test runner downloads screenshots and network captures to the designated result directory:
   ```bash
   scp macbook:/tmp/ego-shots/cmd/case-01-*.png ./01-gherkin-result-case-palette-trigger-keyboard-and-topbar/screenshots/
   ```
4. **Result Directory Specification**:
   - Each Gherkin case corresponds to an execution result directory named `0X-gherkin-result-case-<slug>/`.
   - Result directories are **NEVER created as empty placeholders**. They are instantiated only by the test execution runner upon executing the suite.

---

## 5. Traceability & Code Coverage Matrix

| Original Scenario ID | Original Title | New Modular Gherkin Case | Real Code Reference & Invariant Hardening |
|:---|:---|:---|:---|
| E2E-CMD-01 | Open Palette via Keyboard Shortcut | `01-gherkin-case-palette-trigger-keyboard-and-topbar.md` | `assets/radar.js:6210-6225` (`(ev.metaKey || ev.ctrlKey) && ev.key === 'k'`) |
| E2E-CMD-02 | Open Palette via Topbar Button | `01-gherkin-case-palette-trigger-keyboard-and-topbar.md` | `assets/radar.js:5200-5205` (`act === "open-cmd-palette"`, `toggleCommandPalette(true)`) |
| E2E-CMD-03 | Query Search & Result Filtering | `02-gherkin-case-query-search-and-filtering.md` | `assets/radar.js:6230-6260` (`getCmdItems(query)`, selection range caret preservation) |
| E2E-CMD-04 | Arrow Key Traversal & Selected State | `03-gherkin-case-arrow-traversal-and-wraparound.md` | `assets/radar.js:6270-6290` (`moveCmdSelection(1)`, `(cur + 1) % items.length`) |
| E2E-CMD-05 | Command Execution via Enter Key | `04-gherkin-case-command-execution-enter-and-click.md` | `assets/radar.js:6300-6320` (`executeCmdSelection()`, `items[selIdx].action()`) |
| E2E-CMD-06 | Command Execution via Mouse Click | `04-gherkin-case-command-execution-enter-and-click.md` | `assets/radar.js:6325-6340` (`select-cmd-item` click delegation) |
| E2E-CMD-07 | Dismissal & Focus Restoration | `05-gherkin-case-palette-dismissal-and-focus-recovery.md` | `assets/radar.js:6350-6375` (`previousActiveElement.focus()`, fallback focus) |
| E2E-CMD-08 | Keyboard Accessibility Bridge | `06-gherkin-case-keyboard-accessibility-bridge.md` | `assets/radar.js:6380-6405` (Global `Enter`/`Space` delegation on `[data-action]`) |
| E2E-CMD-09 | Regex Metacharacter Query Immunity | `07-gherkin-case-regex-metacharacter-query-immunity.md` | `assets/radar.js:6240-6250` (`String.prototype.indexOf` instead of `new RegExp`) |
| E2E-CMD-10 | Empty Search State & Enter Key Safety | `08-gherkin-case-empty-state-and-enter-guard.md` | `assets/radar.js:6305-6315` (`if (items[selIdx])` null guard on empty Enter) |
| E2E-CMD-11 | Modal Stacking & Layered Focus Trap | `09-gherkin-case-modal-stacking-and-z-index-layering.md` | `assets/radar.css:1240-1260` (`z-index: 10000`, underlying `#modalHolder` preservation) |
| E2E-CMD-12 | Container Overflow & Fold Traversal | `03-gherkin-case-arrow-traversal-and-wraparound.md` | `assets/radar.css:1265-1280` (`.cmd-body` `max-height: 380px; overflow-y: auto`) |
