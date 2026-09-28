# Test Case: Rapid Tab Switching Concurrency, `bootSeq` Monotonic Guard & State Cleanup

## 1. Case ID & Purpose
- **Case ID:** `TC-NAV-08-RAPID-TAB-CLICK-RACE`
- **Purpose:** Verify system resilience against race conditions during rapid, consecutive tab switching (e.g. 8 tabs clicked within < 500ms), asserting that the monotonic `bootSeq` sequence lock discards stale asynchronous bootstrap decisions, preserves DOM integrity, flushes active modal holders, and lands deterministically on the final selected tab without UI thrashing or orphaned subviews.

---

## 2. Tester Brief
The tester (human or AI agent) will navigate to `[APP_URL]/#/[SLUG]/overview`, programmatically trigger rapid consecutive click events across 8 distinct sidebar items in sub-second bursts, monitor the increment of `bootSeq`, assert that stale asynchronous resolutions are safely aborted, verify that the final active tab matches the last clicked item (`skills`), assert that `#modalHolder` is completely empty, and verify that no race condition exceptions or visual corruption occur.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Brand `"[SLUG]"`, tab `"overview"`
- **Rapid Click Sequence:** `['aei', 'volumes', 'agentanalytics', 'opportunities', 'workflows', 'pages', 'dashboards', 'skills']`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[BURST_COUNT]`: Number of tabs in rapid sequence (8)
  - `[FINAL_TAB]`: The final target tab in the sequence (`skills`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Sidebar Shell - Rapid Tab Switching Concurrency and Race Immunity

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the initial view is mounted on tab "overview"

  @concurrency @stress @race-lock @positive
  Scenario: Rapid consecutive tab clicks settle on the final tab without race errors
    When the user triggers rapid consecutive clicks across 8 sidebar tabs in under 500ms:
      | aei            |
      | volumes        |
      | agentanalytics |
      | opportunities  |
      | workflows      |
      | pages          |
      | dashboards     |
      | skills         |
    Then the asynchronous bootstrap guard "bootSeq" should increment for each switch
    And stale data resolutions from prior clicks should be discarded
    And the application should settle on the final tab "skills"
    And "window.state.tab" should equal "skills"
    And the sidebar item '.side-item[data-key="skills"]' should have class "active"
    And the modal holder element "#modalHolder" should have 0 children
    And subview states "skills.open", "dash.open", and "pages.open" should be null
    And the skills container should be rendered in the main view
```

---

## 5. Visual Checks
- **Settled Viewport State:**
  - After rapid clicking ceases, the DOM displays only the final tab (`skills`).
  - No leftover card fragments or charts from intermediate views (`dashboards`, `workflows`) linger in `.main`.
  - Active indicator is affixed solely to the `skills` tab in the sidebar.

---

## 6. Data & Network Checks
- **Concurrency & State Assertions:**
  ```javascript
  const activeItem = document.querySelector('.side-item.active');
  const modalHolder = document.getElementById('modalHolder');
  
  assert(window.state.tab === 'skills', "Final state.tab must be 'skills'");
  assert(activeItem && activeItem.getAttribute('data-key') === 'skills', "Active sidebar element must be 'skills'");
  assert((modalHolder?.children.length || 0) === 0, "modalHolder must be empty");
  assert(window.state.skills?.open === null, "skills.open must be null");
  assert(window.state.dash?.open === null, "dash.open must be null");
  assert(window.state.pages?.open === null, "pages.open must be null");
  ```
- **Error Telemetry:**
  - Browser console contains 0 uncaught promises or `bootSeq` race exceptions.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-rapid-tab-click-race-concurrency/`
- **Required Artifacts:**
  - `result.md`: Timing trace of the 8-tab burst sequence, settle duration, and final state.
  - `evidence.json`: Dumps of sequence IDs, final `window.state`, and DOM tree validation.
  - `screenshots/08-rapid-switching-settled.png`: Screen capture of the cleanly settled final view.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/nav/case-08-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
