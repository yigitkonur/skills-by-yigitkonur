# Test Case: Desktop Sidebar Collapse, Mini-State & Floating Reopen Button

## 1. Case ID & Purpose
- **Case ID:** `TC-NAV-04-DESKTOP-SIDEBAR-COLLAPSE`
- **Purpose:** Verify that clicking the desktop collapse button (`.foot-btn[data-action="side-collapse"]`) in the sidebar footer toggles `window.state.sideCollapsed`, applies the CSS class `.side-collapsed` to `document.body`, hides the sidebar navigation (`display: none`), and mounts the floating `.side-reopen` trigger button. Verify that clicking `.side-reopen` restores the expanded sidebar.

---

## 2. Tester Brief
The tester (human or AI agent) will navigate to `[APP_URL]/#/[SLUG]/overview` in desktop viewport (width >= 1024px), locate the collapse button in the sidebar footer, trigger collapse, assert that `document.body` receives `.side-collapsed` and `.sidebar` is hidden, assert that the reopen button `.side-reopen` appears in the viewport corner, click `.side-reopen`, and assert that the sidebar expands back to its default state.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Viewport Size:** Desktop (`1440x900` or width >= 1024px)
- **Initial State:** `state.sideCollapsed === false`, `body.classList.contains("side-collapsed") === false`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[VIEWPORT_SIZE]`: Desktop resolution (`1440x900`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Sidebar Navigation - Desktop Collapse and Reopen Lifecycle

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview" with viewport width 1440
    And the desktop sidebar ".sidebar" is visible and expanded

  @desktop @collapse @positive
  Scenario: Collapsing the sidebar hides navigation and reveals reopen trigger
    When the user clicks the footer button ".foot-btn[data-action='side-collapse']"
    Then "window.state.sideCollapsed" should equal true
    And the body element should have class "side-collapsed"
    And the computed display of ".sidebar" should be "none"
    And the reopen button ".side-reopen[data-action='side-collapse']" should be visible

  @desktop @expand @positive
  Scenario: Clicking the reopen button restores the full sidebar layout
    Given the sidebar is currently collapsed with class "side-collapsed" on body
    When the user clicks the floating reopen button ".side-reopen"
    Then "window.state.sideCollapsed" should equal false
    And the body element should not have class "side-collapsed"
    And the computed display of ".sidebar" should not be "none"
    And the reopen button ".side-reopen" should no longer exist in the DOM
```

---

## 5. Visual Checks
- **Collapsed Viewport:**
  - Sidebar `.sidebar` is completely hidden without partial clipping or horizontal scrollbars.
  - Main content container `.main` expands smoothly to occupy the recovered screen width.
  - Floating button `.side-reopen` renders anchored at top-left (`left: 12px; top: 12px`) with panel icon.
- **Reopened Viewport:**
  - Sidebar returns to full width (240px) with all 15 tab rows intact.
  - Floating reopen button disappears cleanly.

---

## 6. Data & Network Checks
- **DOM & CSS Computed Assertions:**
  ```javascript
  const sidebar = document.querySelector('.sidebar');
  const reopenBtn = document.querySelector('.side-reopen');
  const isCollapsed = document.body.classList.contains('side-collapsed');
  
  if (window.state.sideCollapsed) {
    assert(isCollapsed === true, "body must have side-collapsed class");
    assert(window.getComputedStyle(sidebar).display === 'none', "sidebar display must be 'none'");
    assert(reopenBtn !== null, "side-reopen button must be rendered in DOM");
  } else {
    assert(isCollapsed === false, "body must not have side-collapsed class");
    assert(window.getComputedStyle(sidebar).display !== 'none', "sidebar display must not be 'none'");
    assert(reopenBtn === null, "side-reopen button must be removed from DOM");
  }
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-desktop-sidebar-collapse-and-expand/`
- **Required Artifacts:**
  - `result.md`: Execution outcome, timing, visual transition verifications.
  - `evidence.json`: Captured computed styles and state attributes.
  - `screenshots/04-sidebar-expanded.png`: Desktop screen before collapse.
  - `screenshots/04-sidebar-collapsed.png`: Full-bleed content with `.side-reopen` button.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/nav/case-04-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
