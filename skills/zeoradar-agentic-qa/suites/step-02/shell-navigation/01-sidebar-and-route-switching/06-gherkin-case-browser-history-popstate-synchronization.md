# Test Case: Browser History API (Back/Forward), Popstate Handling & State Restoration

## 1. Case ID & Purpose
- **Case ID:** `TC-NAV-06-BROWSER-HISTORY-POPSTATE`
- **Purpose:** Verify that client-side route transitions push distinct history entries onto the browser History stack (`window.history.pushState`), and that subsequent user navigation via browser Back and Forward buttons fires `popstate`, correctly parses the target route, restores `window.state.tab`, updates the active sidebar item, and remounts the view without triggering a disruptive full-page reload.

---

## 2. Tester Brief
The tester (human or AI agent) will navigate across three sequential tabs (`overview` -> `aei` -> `opportunities`), trigger browser history Back navigation (`window.history.back()`), assert that the view transitions back to `aei` and sidebar highlights `aei`, trigger Back again to reach `overview`, and trigger browser history Forward navigation (`window.history.forward()`) to re-advance to `aei` and `opportunities`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Brand `"[SLUG]"`, tab `"overview"`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[START_TAB]`: Initial tab (`overview`)
  - `[MID_TAB]`: Intermediate tab (`aei`)
  - `[FINAL_TAB]`: Destination tab (`opportunities`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Sidebar Shell - Browser History API Navigation and Popstate Synchronization

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And "window.state.tab" is "overview"

  @history @popstate @positive
  Scenario: Sequential navigation pushes history states that can be traversed back and forward
    When the user clicks the sidebar item '.side-item[data-key="aei"]'
    Then "window.state.tab" should equal "aei"
    And the URL path should end with "/[SLUG]/visibility"
    When the user clicks the sidebar item '.side-item[data-key="opportunities"]'
    Then "window.state.tab" should equal "opportunities"
    And the URL path should end with "/[SLUG]/opportunities"

    When the user clicks the browser Back button
    Then the router should intercept the popstate event
    And "window.state.tab" should equal "aei"
    And the sidebar element '.side-item[data-key="aei"]' should have class "active"
    And the URL path should end with "/[SLUG]/visibility"

    When the user clicks the browser Back button again
    Then "window.state.tab" should equal "overview"
    And the sidebar element '.side-item[data-key="overview"]' should have class "active"
    And the URL path should end with "/[SLUG]"

    When the user clicks the browser Forward button
    Then "window.state.tab" should equal "aei"
    And the sidebar element '.side-item[data-key="aei"]' should have class "active"
```

---

## 5. Visual Checks
- **Active Tab Reflection:**
  - On each Back / Forward transition, the `.active` class instantly moves to the target sidebar item.
- **Content Replacement:**
  - Old tab view unmounts cleanly, and the restored tab view renders without residual DOM nodes from the superseded page.
- **No Page Flash:**
  - Popstate transitions occur smoothly in-memory without a browser white-screen reload.

---

## 6. Data & Network Checks
- **History & State Assertions:**
  ```javascript
  // Verify state matches current location after popstate
  const currentPath = window.location.pathname;
  const parsed = ZeoRouter.parse(currentPath, window.location.search, window.location.hash);
  assert(window.state.tab === parsed.tab, "state.tab must match parsed URL tab");
  assert(document.querySelector('.side-item.active').getAttribute('data-key') === parsed.tab || 
        (parsed.tab === 'aei' && document.querySelector('.side-item.active').getAttribute('data-key') === 'aei'),
        "Active sidebar item must match current history route");
  ```
- **Console Monitoring:**
  - Verify zero unhandled exceptions or listener errors thrown during popstate dispatch.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-browser-history-popstate-synchronization/`
- **Required Artifacts:**
  - `result.md`: History traversal trace table with step times and state comparisons.
  - `evidence.json`: Captured history state transitions and router parse outputs.
  - `screenshots/06-history-back-aei.png`: View restored after first Back navigation.
  - `screenshots/06-history-back-overview.png`: View restored after second Back navigation.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/nav/case-06-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
