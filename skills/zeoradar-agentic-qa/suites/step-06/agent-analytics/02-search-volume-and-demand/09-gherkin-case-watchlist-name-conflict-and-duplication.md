# Case 09: Watchlist Duplicate Name Conflicts & Atomic Duplication

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-09`
- **Purpose**: Verify that creating or renaming a watchlist to an existing name within the project triggers the controlled `duplicate_list_name` error protocol, maps the error code to localized copy without leaking database exception traces, rolls back optimistic mutation entries (`kwl_opt_*`) without ghost lists, and verifies atomic server-side watchlist duplication via the kebab menu action.

## 2. Tester Brief
The tester navigates to the Watchlists tab or launches the Bulk Save modal, enters an existing watchlist name (e.g. `"Core Products"`), and attempts to confirm the save. The tester intercepts or mocks `callCommand("upsert-keyword-list")` returning error code `'duplicate_list_name'`, validates that the error toast displays user-friendly localized text, verifies that optimistic entries (`kwl_opt_*`) are cleanly evicted, and tests clicking the "Duplicate List" kebab action on an existing list.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Existing List Name: `"Core Products"`
  - Error Codes: `duplicate_list_name`, `validation_failed`, `not_found`
- **Prerequisites**:
  - Watchlists view active.

## 4. Gherkin Scenario

```gherkin
Feature: Watchlist Conflict Handling & Atomic Duplication
  As an Enterprise Product Manager
  I want duplicate watchlist names to be gracefully rejected with localized guidance
  And I want one-click atomic duplication of existing monitoring lists

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    And an existing watchlist named "Core Products" exists in the project

  Scenario Outline: Reject duplicate or invalid watchlist names with localized copy
    When the user attempts to create a watchlist with invalid name or conflict "<error_code>"
    Then the command error mapper "window.volListCmdErrorCopy" should return localized message "<expected_copy_snippet>"
    And an error toast should appear displaying "<expected_copy_snippet>"
    And optimistic list entries with prefix "kwl_opt_" should be rolled back from state
    And no orphaned ghost lists should remain in the UI

    Examples:
      | error_code          | expected_copy_snippet                  |
      | duplicate_list_name | A list with this name already exists   |
      | validation_failed   | Enter a valid list name                |
      | not_found           | This list no longer exists             |

  Scenario: Execute atomic server-side watchlist duplication
    Given the user is on the Watchlists tab "button.volumes-tab-btn[data-tab='watchlists']"
    When the user clicks the kebab menu for watchlist "Core Products"
    And clicks the duplicate action ".vol-kebab-item[data-action='vol-duplicate-list']"
    Then the command "upsert-keyword-list" should be dispatched with "copyFromListId"
    And a duplicated watchlist should appear in the lists grid
    And the duplicated list should contain identical keyword terms
```

## 5. Visual Checks
- **Error Toast**: Clean red notification displaying localized message followed by the error code in parentheses.
- **Optimistic Cleanup**: Failed list disappears smoothly without DOM artifact flashes.
- **Kebab Popover**: Neatly positioned dropdown menu with clear icons for Duplicate and Delete.

## 6. Data and Network Checks
- **Error Mapping Contract**:
  ```javascript
  const enCopy = window.volListCmdErrorCopy("duplicate_list_name");
  assert.ok(enCopy.includes("already exists") || enCopy.includes("zaten var"));
  // Assert no kwl_opt remains in state
  const optLists = (window.volumesState.watchlists || []).filter(l => l.id.startsWith("kwl_opt_"));
  assert.strictEqual(optLists.length, 0);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-watchlist-name-conflict-and-duplication/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-09-duplicate-error-toast.png`
     - `/tmp/ego-shots/tc-vol-09-duplicated-watchlist.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-09-*.png ./02-gherkin-result-case-watchlist-name-conflict-and-duplication/
     ```
