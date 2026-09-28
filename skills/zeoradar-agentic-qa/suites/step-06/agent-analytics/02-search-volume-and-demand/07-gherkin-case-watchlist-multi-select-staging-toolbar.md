# Case 07: Watchlist Multi-Select Staging & Sticky Bulk Action Toolbar

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-07`
- **Purpose**: Verify that the master select-all checkbox (`vol-head-check`) and individual prompt row checkboxes (`vol-row-check`) in the Top 25 detected prompts table correctly stage candidate prompts into `volumesState.selectedPromptIds`, slide the sticky bulk action toolbar (`.vol-bulk-toolbar`) into view with dynamic selection counts, launch the Bulk Save modal with tag preview chips, and successfully create or append to watchlists while clearing staged selections.

## 2. Tester Brief
The tester views the Top 25 prompts table, clicks the header master checkbox to select all 25 visible prompts, and verifies that the sticky bulk action toolbar appears at the viewport bottom displaying "25 prompts selected". The tester clicks the "Save to Watchlist" button on the toolbar, confirms that the bulk save modal opens displaying preview tags for the staged terms, enters a new watchlist name (e.g. `"Q4 High Intent Focus"`), confirms the save, and validates that the modal closes and the toolbar dismisses with cleared checkboxes.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Staged Prompts Count: 25
  - New Watchlist Name: `"Q4 High Intent Focus"`
- **Prerequisites**:
  - Explore & Trends table rendered.

## 4. Gherkin Scenario

```gherkin
Feature: Watchlist Multi-Select Staging & Bulk Action Toolbar
  As an Enterprise SEO Lead
  I want to multi-select and stage high-potential consumer prompts
  So that I can bulk save them into custom project monitoring watchlists

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    And the Top 25 Consumer Prompts table is displayed
    And the sticky bulk toolbar ".vol-bulk-toolbar" is currently hidden

  Scenario: Stage all 25 prompts using master select-all checkbox
    When the user clicks the master checkbox "input.vol-head-check[data-action='vol-toggle-select-all']"
    Then all 25 visible row checkboxes "input.vol-row-check" should become checked
    And "window.volumesState.selectedPromptIds" should contain 25 active terms
    And the sticky bulk toolbar ".vol-bulk-toolbar" should slide into view
    And the toolbar counter should state "25 prompts selected"

  Scenario: Uncheck master checkbox to clear all staged selections
    Given all 25 prompts are currently selected and the bulk toolbar is visible
    When the user clicks the master checkbox "input.vol-head-check" again
    Then all row checkboxes should become unchecked
    And "window.volumesState.selectedPromptIds" should be empty
    And the sticky bulk toolbar should be hidden from view

  Scenario: Bulk save staged prompts into a new custom watchlist
    Given 25 prompts are staged and the bulk toolbar is visible
    When the user clicks the toolbar button "button[data-action='vol-open-bulk-save']"
    Then the Bulk Save modal ".vol-md-modal" should open
    And the modal should display preview chip tags for the selected terms
    When the user enters "Q4 High Intent Focus" into "#volBulkNewListName"
    And the user clicks the confirm button "button[data-action='vol-confirm-bulk-save']"
    Then the new watchlist should be created
    And the Bulk Save modal should close
    And the staged selection should be cleared
    And the sticky bulk toolbar should dismiss
```

## 5. Visual Checks
- **Master Checkbox**: Renders clean box in table header column 1.
- **Sticky Bulk Toolbar**: Floats at the bottom edge with dark background, contrasting white count text, and action buttons (`.btn.black`).
- **Modal Chips**: Multi-color or muted tags showing query text with ellipsis for overflow.

## 6. Data and Network Checks
- **Selection State Properties**:
  ```javascript
  const sel = window.volumesState.selectedPromptIds;
  const count = Object.keys(sel).filter(k => sel[k]).length;
  assert.strictEqual(count, 25);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-watchlist-multi-select-staging-toolbar/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-07-bulk-toolbar-active.png`
     - `/tmp/ego-shots/tc-vol-07-bulk-modal-chips.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-07-*.png ./02-gherkin-result-case-watchlist-multi-select-staging-toolbar/
     ```
