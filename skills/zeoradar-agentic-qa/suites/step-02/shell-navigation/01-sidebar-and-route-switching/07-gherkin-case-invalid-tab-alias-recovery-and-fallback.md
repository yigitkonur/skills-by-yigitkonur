# Test Case: Deep-Linking Fallback for Invalid Tab Aliases & Hash Fallback

## 1. Case ID & Purpose
- **Case ID:** `TC-NAV-07-INVALID-TAB-FALLBACK`
- **Purpose:** Verify router resiliency when users deep-link directly into unrecognized tab aliases (e.g. `/[SLUG]/invalid-slug-xyz`), ensuring the shell gracefully falls back to the default AEI Visibility view (`sideKey = "aei"`) rather than crashing, while also asserting that legacy aliases (`brand-hub` -> `kb`, `agent-analytics` -> `agentanalytics`) and hash-based URLs (`#/[SLUG]/opportunities`) resolve correctly.

---

## 2. Tester Brief
The tester (human or AI agent) will navigate directly to an invalid URL (`[APP_URL]/#/[SLUG]/nonexistent-view-123`), observe the router parse result, verify that the application renders the AEI Visibility view with filterbar rather than a white screen or uncaught exception, navigate to legacy aliases (`[APP_URL]/#/[SLUG]/brand-hub`), assert mapping to `kb`, and navigate to hash route (`[APP_URL]/#/[SLUG]/opportunities`), asserting accurate resolution under hash fallback mode.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/nonexistent-view-123`
- **Initial State:** Direct URL entry into browser address bar
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[INVALID_TAB]`: Unrecognized tab slug (`nonexistent-view-123`, `foo-bar-tab`)
  - `[LEGACY_TAB]`: Deprecated alias (`brand-hub`, `agent-analytics`)
  - `[RESOLVED_TAB]`: Canonical internal tab key (`kb`, `agentanalytics`, `aei`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Router Fallback - Invalid Tab Aliases, Legacy Mappings & Hash Routing

  Background:
    Given the application shell is running on "[DOMAIN]"

  @resilience @routing @fallback
  Scenario: Deep-linking to an unrecognized tab alias falls back safely to AEI Visibility view
    When the user navigates directly to "[APP_URL]/#/[SLUG]/nonexistent-view-123"
    Then the router should parse the tab as "nonexistent-view-123"
    And the view renderer should execute the safe fallback setting the active sidebar item to "aei"
    And the AEI visibility container should be mounted with a filterbar
    And no uncaught JavaScript exceptions should be logged in the console

  @aliases @routing @positive
  Scenario Outline: Legacy tab aliases map automatically to canonical internal tabs
    When the user navigates directly to "[APP_URL]/#/[SLUG]/<legacy_tab>"
    Then "window.state.tab" should equal "<canonical_tab>"
    And the sidebar item '.side-item[data-key="<canonical_tab>"]' should receive class "active"

    Examples:
      | legacy_tab       | canonical_tab    |
      | brand-hub        | kb               |
      | brandhub         | kb               |
      | agent-analytics  | agentanalytics   |
      | visibility       | aei              |

  @hash-routing @fallback @positive
  Scenario: Hash-formatted URLs parse and mount appropriate brand tabs
    When the user navigates directly to "[APP_URL]/#/[SLUG]/opportunities"
    Then the router should identify hash routing mode
    And "window.state.slug" should equal "[SLUG]"
    And "window.state.tab" should equal "opportunities"
    And the opportunities view container ".opps-container" should be mounted
```

---

## 5. Visual Checks
- **Fallback View Presentation:**
  - Upon invalid tab navigation, AEI Visibility view renders with its standard header, metric cards, and filterbar.
  - Active sidebar indicator settles cleanly on Answer Engine Insights (`.side-item[data-key="aei"].active`).
- **No White Screen / Broken Layout:**
  - Viewport remains fully interactive without error banners or frozen spinners.

---

## 6. Data & Network Checks
- **DOM & State Assertions:**
  ```javascript
  // Assert fallback view mounted
  const hasFilterbar = !!document.querySelector('.filterbar');
  const hasContent = !!document.querySelector('.page, .main');
  assert(hasFilterbar && hasContent, "Fallback view must mount filterbar and content");
  
  // Assert alias resolution
  const parsed = ZeoRouter.parse('/' + (window.state.slug || '[SLUG]') + '/brand-hub');
  assert(parsed.tab === 'kb', "brand-hub must alias to kb");
  ```
- **Error Telemetry:**
  - Assert zero `TypeError` or `ReferenceError` events fired in `window.addEventListener('error')`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-invalid-tab-alias-recovery-and-fallback/`
- **Required Artifacts:**
  - `result.md`: Detailed audit of fallback resolution, alias mappings, and hash routing.
  - `evidence.json`: Captured router outputs and console error logs.
  - `screenshots/07-invalid-tab-fallback.png`: Screenshot showing clean AEI view for invalid route.
  - `screenshots/07-hash-route-mounted.png`: Screenshot of `#/[SLUG]/opportunities` loaded.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/nav/case-07-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
