# Case 08: Filtered Watchlist Staging Boundary & Implementation Critique

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-08`
- **Purpose**: Verify the boundary conditions of prompt selection staging when active search queries or intent filters are applied to the Top 25 prompts table, critically evaluating whether the master select-all toggle (`vol-head-check`) operates strictly against visible filtered prompts or across the entire unfiltered catalog slice (`volGetExploreItems().slice(0, 25)`), and ensuring that toolbar clear actions (`vol-clear-selection`) completely purge staged state without orphaned keys.

## 2. Tester Brief
The tester activates an intent filter (e.g. `data-intent="trans"`) so that the table renders a reduced subset of prompts (e.g. 8 rows instead of 25). The tester engages the master checkbox, inspects `window.volumesState.selectedPromptIds` to detect whether selections include hidden prompts from other intents (documenting the implementation characteristic in `volumes-analytics.js` line 4464), checks the bulk toolbar count, tests manual individual row toggles on filtered rows, and clicks "Clear Selection" (`button[data-action="vol-clear-selection"]`) to prove complete state reset.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Active Intent Filter: `trans` (Transactional)
  - Visible Filtered Rows: 8 rows
- **Prerequisites**:
  - Prompt Volumes page loaded.

## 4. Gherkin Scenario

```gherkin
Feature: Filtered Watchlist Staging & Selection Isolation
  As a Quality Assurance Automation Architect
  I want prompt staging to behave predictably when views are filtered
  So that users do not inadvertently stage or save hidden prompts that do not match active filters

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    And the Top 25 prompts table is displayed

  Scenario: Evaluate select-all behavior under active intent filter
    When the user clicks the intent filter pill "button.vol-intent-pill[data-intent='trans']"
    Then the table should only display transactional prompt rows (8 rows)
    When the user clicks the master checkbox "input.vol-head-check[data-action='vol-toggle-select-all']"
    Then the application should update "window.volumesState.selectedPromptIds"
    And the bulk action toolbar ".vol-bulk-toolbar" should appear
    And the tester should record whether staged count reflects visible rows (8) or slice items (25)

  Scenario: Individually stage visible filtered prompts
    Given an active intent filter "trans" displaying 8 rows
    And all selection states are initially cleared
    When the user clicks row checkboxes "input.vol-row-check" for 3 distinct transactional prompts
    Then "window.volumesState.selectedPromptIds" should contain exactly 3 keys
    And the bulk toolbar should state "3 prompts selected"
    And hidden non-transactional prompts should remain unselected

  Scenario: Clear selections via toolbar action button
    Given 3 prompts are staged and the bulk toolbar is displayed
    When the user clicks the clear action button "button[data-action='vol-clear-selection']"
    Then "window.volumesState.selectedPromptIds" should reset to an empty object "{}"
    And the master checkbox "input.vol-head-check" should be unchecked
    And all row checkboxes should be unchecked
    And the sticky bulk toolbar should be completely removed from the viewport
```

## 5. Visual Checks
- **Filtered Table Count**: Table meta badge displays count (e.g. `8 / 25 prompts`).
- **Toolbar Counter**: Accurately reflects staged count text.
- **Checkbox Synchronization**: Row checkboxes visually reflect state without desync after filter changes.

## 6. Data and Network Checks
- **State Property Assertions**:
  ```javascript
  // After clearing
  assert.strictEqual(Object.keys(window.volumesState.selectedPromptIds || {}).length, 0);
  assert.strictEqual(document.querySelector('.vol-head-check').checked, false);
  assert.strictEqual(document.querySelector('.vol-bulk-toolbar'), null);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-filtered-watchlist-staging-boundary/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-08-filtered-staging.png`
     - `/tmp/ego-shots/tc-vol-08-cleared-selection.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-08-*.png ./02-gherkin-result-case-filtered-watchlist-staging-boundary/
     ```
