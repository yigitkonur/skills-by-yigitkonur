# Test Case: Responsive Mobile Drawer Toggle, Overlay Backdrop & Auto-Dismiss

## 1. Case ID & Purpose
- **Case ID:** `TC-NAV-05-MOBILE-DRAWER-LIFECYCLE`
- **Purpose:** Verify the responsive mobile navigation drawer lifecycle on narrow viewports (< 1024px), ensuring that tapping the hamburger button (`.nav-toggle[data-action="side-toggle"]`) toggles `body.side-open`, tapping the overlay backdrop (`.side-backdrop[data-action="side-close"]`) dismisses the drawer, and selecting any navigation tab item auto-dismisses the drawer while navigating.

---

## 2. Tester Brief
The tester (human or AI agent) will resize the viewport to mobile emulation (`390x844`), assert that the hamburger toggle is displayed in the topbar, click `.nav-toggle`, verify that `document.body` gains `.side-open` and the sidebar slides into view, click the overlay backdrop to verify dismissal, reopen the drawer, click a navigation tab (`.side-item[data-key="dashboards"]`), and assert that `.side-open` is automatically removed as the new tab mounts.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Viewport Size:** Mobile (`390x844` or width < 1024px)
- **Initial State:** `body.classList.contains("side-open") === false`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[VIEWPORT_SIZE]`: Mobile emulation (`390x844`)
  - `[TARGET_TAB]`: Navigation tab selected inside drawer (`dashboards`, `opportunities`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Sidebar Navigation - Mobile Drawer Responsive Toggle and Auto-Dismiss

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview" with mobile viewport width 390
    And the mobile hamburger toggle ".nav-toggle" is visible in the topbar

  @mobile @drawer @positive
  Scenario: Toggling hamburger button opens the slide-in navigation drawer
    When the user clicks the hamburger button ".nav-toggle[data-action='side-toggle']"
    Then the body element should have class "side-open"
    And the backdrop element ".side-backdrop" should be displayed
    When the user clicks the backdrop element ".side-backdrop[data-action='side-close']"
    Then the body element should not have class "side-open"

  @mobile @drawer @auto-dismiss @positive
  Scenario Outline: Selecting a navigation tab inside mobile drawer automatically dismisses drawer
    Given the mobile drawer is open with class "side-open" on body
    When the user clicks the drawer navigation item '.side-item[data-key="<target_tab>"]'
    Then the body element should not have class "side-open"
    And "window.state.tab" should equal "<target_tab>"
    And the view container for "<target_tab>" should be mounted

    Examples:
      | target_tab   |
      | dashboards   |
      | opportunities|
      | pages        |
```

---

## 5. Visual Checks
- **Topbar Hamburger Button:**
  - `.nav-toggle` is visible with standard menu bars icon.
- **Drawer Animation & Layering:**
  - Sidebar slides in from left with elevation shadow over the main viewport.
  - Backdrop `.side-backdrop` covers the remainder of the viewport with semi-transparent scrim (`rgba(0, 0, 0, 0.4)`).
- **Auto-Dismiss:**
  - On tab selection, drawer closes immediately without flickering or obstructing the target view.

---

## 6. Data & Network Checks
- **DOM & Class Invariants:**
  ```javascript
  const body = document.body;
  const isOpen = body.classList.contains('side-open');
  if (isOpen) {
    const backdrop = document.querySelector('.side-backdrop');
    assert(backdrop !== null, "Backdrop must exist when drawer is open");
  } else {
    assert(!body.classList.contains('side-open'), "side-open class must be removed");
  }
  ```
- **State Invariants:**
  - `window.state.tab` correctly updates to `<target_tab>`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-mobile-drawer-responsive-lifecycle/`
- **Required Artifacts:**
  - `result.md`: Detailed test step results on mobile emulation viewport.
  - `evidence.json`: Captured classList states and touch event telemetry.
  - `screenshots/05-mobile-drawer-open.png`: Mobile view showing slide-in drawer and backdrop.
  - `screenshots/05-mobile-drawer-dismissed.png`: Target dashboard loaded with drawer closed.
- **MacBook Execution Protocol:** Ego Browser captures mobile display screenshots to `/tmp/ego-shots/nav/case-05-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
