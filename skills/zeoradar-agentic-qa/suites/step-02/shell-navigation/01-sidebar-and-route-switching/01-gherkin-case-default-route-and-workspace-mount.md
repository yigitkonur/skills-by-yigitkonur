# Test Case: Default Route, Workspace Resolution & Active Overview State

## 1. Case ID & Purpose
- **Case ID:** `TC-NAV-01-DEFAULT-ROUTE-MOUNT`
- **Purpose:** Verify that navigating to the root brand asset URL (`[APP_URL]/#/[SLUG]`) resolves dynamically to the default `"overview"` tab, marks the corresponding sidebar navigation item as active, sets up the workspace profile context, and mounts the primary dashboard container without route errors.

---

## 2. Tester Brief
The tester (human or AI agent) will navigate to `[APP_URL]/#/[SLUG]/overview` , observe the initial client-side router resolution, verify that `window.state.tab` equals `"overview"`, verify that the sidebar item `.side-item[data-key="overview"]` receives the `.active` class, and assert that the topbar and main content areas reflect the resolved brand workspace.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview` 
- **Initial State:** Clean session, `window.state.slug === null` prior to navigation
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test 
  - `[BRAND_SLUG]`: Target brand workspace slug (`[SLUG]`)
  - `[EXPECTED_TAB]`: Default tab identifier (`overview`)
  - `[BRAND_LABEL]`: User-facing brand title (`[BRAND]`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Sidebar Shell - Default Route Resolution and Workspace Mounting

  Background:
    Given the application shell is running on "[APP_URL]"
    And the browser initializes with a clean storage state

  @sanity @routing @positive
  Scenario Outline: Navigating to root brand URL resolves to Overview and activates sidebar item
    When the user navigates to "[APP_URL]/#/<brand_slug>/overview"
    Then the router should parse the URL and set "window.state.slug" to "<brand_slug>"
    And the router should assign "window.state.tab" to "<expected_tab>"
    And the sidebar element '.side-item[data-key="<expected_tab>"]' should have class "active"
    And the brand switcher trigger ".side-asset span" should display "<brand_label>"
    And the main container ".main" should render the dashboard view

    Examples:
      | brand_slug  | expected_tab | brand_label  |
      | [SLUG]      | overview     | [BRAND]       |
      | ulker       | overview     | Ülker        |
      | superfresh  | overview     | SuperFresh   |
```

---

## 5. Visual Checks
- **Sidebar Structure:**
  - Sidebar container `.sidebar` is visible on desktop viewports (`display: flex` or `width: 240px`).
  - Active tab `.side-item[data-key="overview"].active` has high-contrast background styling (`var(--bg-active)` or subtle border accent).
- **Brand Identity Element:**
  - Element `.side-asset` renders brand monogram / favicon and brand label text `<brand_label>`.
  - Dropdown indicator icon is visible next to the brand name.
- **Main Viewport Layout:**
  - Topbar `.topbar` displays the brand title and search trigger.
  - Container `.main` contains the overview dashboard KPI strip and charts.

---

## 6. Data & Network Checks
- **DOM Assertions:**
  ```javascript
  const activeItem = document.querySelector('.side-item.active');
  const brandLabel = document.querySelector('.side-asset span');
  assert(activeItem !== null, "An active sidebar item must exist");
  assert(activeItem.getAttribute('data-key') === 'overview', "Active item key must be 'overview'");
  assert(brandLabel && brandLabel.textContent.trim().length > 0, "Brand label must not be empty");
  ```
- **State Assertions:**
  ```javascript
  assert(window.state.route === 'app', "state.route must equal 'app'");
  assert(window.state.slug === '[BRAND_SLUG]', "state.slug must match target brand");
  assert(window.state.tab === 'overview', "state.tab must default to 'overview'");
  ```
- **Network Telemetry:**
  - Data bootstrap request for the active profile completes with HTTP 200.
  - No 404 or unhandled rejection errors logged in browser console.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-default-route-and-workspace-mount/`
- **Required Artifacts:**
  - `result.md`: Execution outcome, timing, environment specs, pass/fail status.
  - `evidence.json`: Serialized output of `window.state`, active DOM element attributes, and console log trace.
  - `screenshots/01-default-route-mounted.png`: High-resolution viewport capture of the loaded Overview screen.
- **MacBook Execution Protocol:** Ego Browser runs on the physical MacBook host. Screenshots captured on the MacBook display (`/tmp/ego-shots/nav/case-01-*.png`) are retrieved via SCP before compiling `result.md`.
