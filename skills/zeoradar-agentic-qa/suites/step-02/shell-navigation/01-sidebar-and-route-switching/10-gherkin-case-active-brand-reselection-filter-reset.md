# Test Case: Active Brand Re-Selection, Filter State Cleansing & Silent URL Invariance

## 1. Case ID & Purpose
- **Case ID:** `TC-NAV-10-ACTIVE-BRAND-RESELECTION-RESET`
- **Purpose:** Verify that re-selecting the currently active brand in the brand switcher (`state.slug === selectedSlug`) triggers a safe workspace state reset: resetting `state.tab` to `"overview"`, flushing active filters (`state.topics`, `state.platforms`, `state.expanded`), clearing dispute/draft states, closing the dropdown, and executing a silent navigation to `/:slug` without creating duplicate browser history entries.

---

## 2. Tester Brief
The tester (human or AI agent) will navigate to `[APP_URL]/#/[SLUG]/overview/opportunities`, apply filters into in-memory state (`state.topics = new Set(['Topic A'])`, `state.platforms = new Set(['ChatGPT'])`), open the brand switcher popover, click the active brand [BRAND] row (`.row[data-slug="[SLUG]"]`), assert that `state.slug` remains `"[SLUG]"`, assert that `state.tab` resets to `"overview"`, verify that filter sets are cleared to `null`, and verify that the URL is updated to `/[SLUG]` without cluttering the browser history stack.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Initial State:** Brand `"[SLUG]"`, tab `"opportunities"`, dirty filter states applied
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[ACTIVE_SLUG]`: Currently active brand workspace (`[SLUG]`)
  - `[EXPECTED_TAB]`: Reset tab destination (`overview`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Brand Switcher - Active Brand Re-Selection and Workspace State Cleanse

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/opportunities"
    And filter criteria are applied to "topics" and "platforms"
    And the current tab is "opportunities"

  @brand-switcher @filter-reset @state-cleansing @positive
  Scenario: Re-selecting the active brand flushes filters and returns to overview
    When the user clicks the brand switcher trigger ".side-asset"
    Then the brand switcher popover "#assetPop" should be visible
    When the user clicks the currently active brand row ".asset-pop .row[data-slug='[SLUG]']"
    Then the popover container "#assetPop" should receive class "hidden"
    And "window.state.slug" should remain "[SLUG]"
    And "window.state.tab" should reset to "overview"
    And "window.state.topics" should be null
    And "window.state.platforms" should be null
    And the URL path should update to "/[SLUG]"
    And the active sidebar item should be '.side-item[data-key="overview"]'
```

---

## 5. Visual Checks
- **Dashboard Viewport Return:**
  - Viewport transitions from Opportunities to Overview dashboard.
  - Sidebar indicator moves from Opportunities back to Overview.
  - Popover dropdown closes completely.
- **Filter Reset:**
  - Any active filter badges or tag pills on the page are removed.

---

## 6. Data & Network Checks
- **State Invariants:**
  ```javascript
  assert(window.state.slug === '[SLUG]', "Slug must remain [SLUG]");
  assert(window.state.tab === 'overview', "Tab must reset to overview");
  assert(window.state.topics === null, "topics must be null");
  assert(window.state.platforms === null, "platforms must be null");
  assert(Object.keys(window.state.expanded || {}).length === 0, "expanded state must be empty");
  ```
- **History Cleanliness:**
  - Silent navigation (`replace` or identical state) does not introduce unnecessary duplicate history states.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-active-brand-reselection-filter-reset/`
- **Required Artifacts:**
  - `result.md`: Evaluation trace verifying tab reset, filter clearing, and history behavior.
  - `evidence.json`: Captured state snapshot before and after active brand re-selection.
  - `screenshots/10-brand-reselected-overview.png`: Overview dashboard displayed after reselection.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/nav/case-10-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
