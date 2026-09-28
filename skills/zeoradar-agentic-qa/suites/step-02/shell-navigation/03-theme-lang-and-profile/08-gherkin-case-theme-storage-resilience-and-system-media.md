# Test Case: Storage-Resilient Theme Fallback & Dynamic OS `prefers-color-scheme` Binding

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-08-THEME-STORAGE-MEDIA-SCHEME`
- **Purpose:** Verify theme engine resilience under restricted storage environments (where `localStorage.setItem` throws or storage is cleared) ensuring non-disruptive theme switching, and assert dynamic two-way binding with the OS color scheme (`window.matchMedia("(prefers-color-scheme: dark)")`) when `state.theme === "system"`, while confirming that explicit `"light"` or `"dark"` user selections ignore OS-level media changes.

---

## 2. Tester Brief
The tester (human or AI agent) will clear/mock localStorage throwing in private browsing mode, invoke `applyTheme('dark')`, assert that `document.body` gains `.dark` without throwing exceptions, set theme to `"system"`, dispatch an OS color scheme change event via `window.matchMedia`, assert that `document.body` dynamically synchronizes with the simulated OS dark/light mode, set theme explicitly to `"light"`, and verify that OS changes no longer override explicit user choice.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** `localStorage` mocked or cleared
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[MEDIA_SCHEME]`: Emulated OS color scheme (`dark`, `light`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Theme Engine - Storage Resilience and Dynamic OS Media Scheme Binding

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"

  @resilience @storage @positive
  Scenario: Theme changes succeed without error even when localStorage is blocked or unavailable
    When the localStorage write throws a QuotaExceededError or is inaccessible
    And the user switches theme to "dark"
    Then no JavaScript exception should be thrown
    And the body element should have class "dark"
    And "window.state.theme" should equal "dark"

  @system-theme @media-query @positive
  Scenario: Setting theme to system dynamically binds to OS prefers-color-scheme
    When the user sets the theme mode to "system"
    Then "window.state.theme" should equal "system"
    When the operating system switches to "dark" mode via prefers-color-scheme
    Then the body element should have class "dark"
    When the operating system switches to "light" mode via prefers-color-scheme
    Then the body element should not have class "dark"

  @explicit-override @positive
  Scenario: Explicit light mode choice is preserved regardless of OS appearance shifts
    Given the user explicitly sets theme to "light"
    When the operating system changes to "dark" mode via prefers-color-scheme
    Then the body element should not have class "dark"
    And "window.state.theme" should remain "light"
```

---

## 5. Visual Checks
- **Dynamic Transition:**
  - When in system mode, toggling the OS appearance instantly alters CSS variables without page refresh or visual stutter.

---

## 6. Data & Network Checks
- **Media Query Assertions:**
  ```javascript
  const mql = window.matchMedia('(prefers-color-scheme: dark)');
  if (window.state.theme === 'system') {
    assert(document.body.classList.contains('dark') === mql.matches, "System theme must match OS matches");
  } else if (window.state.theme === 'light') {
    assert(!document.body.classList.contains('dark'), "Explicit light must not have dark class");
  }
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-theme-storage-resilience-and-system-media/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of storage failure simulation and matchMedia events.
  - `evidence.json`: Captured media query listener states and classList logs.
  - `screenshots/08-system-theme-synced.png`: Screen capture of theme matching OS scheme.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-08-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
