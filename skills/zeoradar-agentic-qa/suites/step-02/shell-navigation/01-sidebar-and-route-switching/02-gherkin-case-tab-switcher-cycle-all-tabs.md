# Test Case: Full 15-Tab Route Navigation, Subview Cleanup & URL Synchronization

## 1. Case ID & Purpose
- **Case ID:** `TC-NAV-02-TAB-SWITCHER-CYCLE`
- **Purpose:** Verify that clicking each of the 15 distinct functional tabs in the sidebar updates `window.state.tab`, resets nested sub-view state (skills, dashboards, pages, brand hub), flushes active modals in `#modalHolder`, synchronizes the browser address bar via `ZeoRouter.navigate()`, and mounts the corresponding view container cleanly.

---

## 2. Tester Brief
The tester (human or AI agent) will iterate through all 15 functional tabs in the sidebar across the three semantic groups (`_analytics`, `_action`, `_context`), asserting that clicking each tab updates the URL to `[APP_URL]/#/[SLUG]/<route_tab>`, activates the corresponding `.side-item`, resets any leftover subview states (`skills.open`, `dash.open`, `pages.open`), and scrolls the viewport to `(0, 0)`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview` 
- **Initial State:** Brand workspace loaded on `"overview"` tab
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[SLUG]`: Active brand slug (`[SLUG]`)
  - `[SIDE_KEY]`: Sidebar element data-key attribute (`aei`, `volumes`, `agentanalytics`, etc.)
  - `[ROUTE_TAB]`: Expected target tab identifier in `window.state.tab` and URL
  - `[VIEW_SELECTOR]`: Unique DOM selector present when view mounts

---

## 4. Gherkin Scenario

```gherkin
Feature: Sidebar Navigation - Complete 15-Tab Switching and State Cleanup

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the initial view is mounted with tab "overview"

  @regression @navigation @positive
  Scenario Outline: Clicking sidebar items updates route, state, and clears subview memory
    When the user clicks the sidebar item '.side-item[data-key="<side_key>"]'
    Then "window.state.tab" should equal "<expected_tab>"
    And the sidebar element '.side-item[data-key="<side_key>"]' should have class "active"
    And the URL path should end with "/[SLUG]/<expected_path>"
    And any active modal in "#modalHolder" should be dismissed
    And the subview state flags "skills.open", "dash.open", and "pages.open" should be null
    And the view container "<view_selector>" should be mounted in ".main"

    Examples: Analytics Group
      | side_key         | expected_tab     | expected_path    | view_selector        |
      | overview         | overview         |                  | .overview-grid, .page|
      | aei              | aei              | visibility       | .aei-container, .page|
      | volumes          | volumes          | volumes          | .designer-container  |
      | agentanalytics   | agentanalytics   | agentanalytics   | .aa-container, .page |

    Examples: Action Group
      | side_key         | expected_tab     | expected_path    | view_selector        |
      | opportunities    | opportunities    | opportunities    | .opps-container      |
      | workflows        | workflows        | workflows        | .wf-container, .page |
      | agents           | agents           | agents           | .agents-page, .page  |

    Examples: Context & Configuration Group
      | side_key         | expected_tab     | expected_path    | view_selector        |
      | pages            | pages            | pages            | .pages-container     |
      | dashboards       | dashboards       | dashboards       | .dash-container      |
      | reports          | reports          | reports          | .reports-container   |
      | kb               | kb               | kb               | .kb-container        |
      | integrations     | integrations     | integrations     | .integrations-page   |
      | skills           | skills           | skills           | .skills-container    |
      | settings         | settings         | settings         | .settings-page       |
      | account          | account          | account          | .account-page        |
```

---

## 5. Visual Checks
- **Active Tab Highlight:**
  - Exactly one `.side-item` carries the `.active` class at any moment.
  - Previous active item reverts to standard inactive hover state.
- **Scroll Position Reset:**
  - Viewport scroll resets to top (`window.scrollY === 0`) upon every tab switch.
- **Header Sections:**
  - Section dividers (`_analytics`, `_action`, `_context`) remain visible as non-clickable header titles.

---

## 6. Data & Network Checks
- **DOM & State Assertions:**
  ```javascript
  const activeTabs = document.querySelectorAll('.side-item.active');
  assert(activeTabs.length === 1, "Only one sidebar tab must be active at a time");
  assert(window.state.tab === '<expected_tab>', "State tab must match clicked item");
  assert(document.getElementById('modalHolder').children.length === 0, "modalHolder must be empty");
  if (window.state.skills) assert(window.state.skills.open === null, "skills.open must be reset");
  if (window.state.dash) assert(window.state.dash.open === null, "dash.open must be reset");
  if (window.state.pages) assert(window.state.pages.open === null, "pages.open must be reset");
  ```
- **Router Synchronization:**
  ```javascript
  const expectedPath = '<expected_path>';
  const expectedSegment = expectedPath ? '/' + expectedPath : '';
  assert(window.location.pathname.endsWith('/' + (window.state.slug || '[SLUG]') + expectedSegment) || window.location.hash.includes(expectedPath));
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-tab-switcher-cycle-all-tabs/`
- **Required Artifacts:**
  - `result.md`: Matrix summary of all 15 tab transitions, response latencies, and pass/fail states.
  - `evidence.json`: Dumps of `window.state` across sequential switches.
  - `screenshots/02-tab-cycle-summary.png`: Composite or collage view of active tab transitions.
- **MacBook Execution Protocol:** Ego Browser runs on physical MacBook host. Screenshots are captured to `/tmp/ego-shots/nav/case-02-*.png` and synced via SCP before compiling `result.md`.
