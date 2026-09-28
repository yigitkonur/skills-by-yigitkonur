# Test Case: Dual Surface Theme Inversion (Light/Dark) via Sidebar Foot and Topbar

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-01-THEME-TOGGLE`
- **Purpose:** Verify theme mode inversion between `"light"` and `"dark"` via both the sidebar footer toggle button (`.foot-btn[data-action="theme-toggle"]`) and the topbar theme toggle button (`.icon-btn.topbar-theme-toggle`), ensuring `document.body` toggles the `.dark` CSS class, `window.state.theme` updates immediately, and the choice is persisted to `localStorage` under keys `zeo_theme` and `zeo-radar-theme`.

---

## 2. Tester Brief
The tester (human or AI agent) will navigate to `[APP_URL]/#/[SLUG]/overview`, verify initial theme state (default light), click `.foot-btn[data-action="theme-toggle"]`, assert that `document.body` gains `.dark` and icon changes to sun, verify `localStorage` persistence, click the topbar theme toggle `.icon-btn.topbar-theme-toggle`, and assert that the theme inverts back to light with `.dark` removed from body.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** `state.theme === "light"` (or initial system), body does not have class `.dark`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[INITIAL_THEME]`: Starting theme (`light`)
  - `[TARGET_THEME]`: Inverted theme (`dark`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Preferences - Dual Surface Theme Inversion (Light/Dark)

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the application is in light mode without class "dark" on body

  @theme @toggle @positive
  Scenario: Toggling theme via sidebar footer activates dark mode and persists preference
    When the user clicks the sidebar footer button ".foot-btn[data-action='theme-toggle']"
    Then the body element should have class "dark"
    And "window.state.theme" should equal "dark"
    And localStorage item "zeo_theme" should equal "dark"
    And the theme toggle button icon should render the "sun" glyph

  @theme @topbar @toggle @positive
  Scenario: Toggling theme via topbar icon button restores light mode
    Given the application is in dark mode with class "dark" on body
    When the user clicks the topbar button ".icon-btn.topbar-theme-toggle"
    Then the body element should not have class "dark"
    And "window.state.theme" should equal "light"
    And localStorage item "zeo_theme" should equal "light"
    And the theme toggle button icon should render the "moon" glyph
```

---

## 5. Visual Checks
- **Dark Mode Presentation:**
  - Background colors switch to deep dark tokens (`var(--bg-main)`, `var(--bg-card)`).
  - Text typography remains crisp with elevated contrast (`var(--ink)`).
  - In dark mode, toggle button shows sun icon (`sun`); in light mode, shows moon icon (`moon`).

---

## 6. Data & Network Checks
- **Storage & State Assertions:**
  ```javascript
  const isDark = document.body.classList.contains('dark');
  const stored = localStorage.getItem('zeo_theme');
  assert(isDark === (window.state.theme === 'dark'), "body class must reflect state.theme");
  assert(stored === window.state.theme, "localStorage must sync with state.theme");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-theme-toggle-light-dark-modes/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of dual surface toggling and storage checks.
  - `evidence.json`: Captured classList, `window.state.theme`, and localStorage dumps.
  - `screenshots/01-theme-dark-applied.png`: Application in full dark mode.
  - `screenshots/01-theme-light-restored.png`: Application restored to light mode.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-01-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
