# Case 09: Edge Server Logs Filtering, Search & Column Sorting

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-09`
- **Purpose**: Verify that the Server Logs tab (`data-tab="logs"`) provides responsive, accurate multi-dimensional filtering across path substrings, HTTP response status codes, and AI crawler platforms, supports sortable table columns (Timestamp, Path, Status), and restores the complete telemetry view upon clicking "Clear All Filters" without residual filter state.

## 2. Tester Brief
The tester switches to the Server Logs tab, enters path substrings (e.g. `/blog`, `/pricing`) into the log search input, and asserts that the log table dynamically filters to matching paths. The tester opens the HTTP status and platform dropdowns, applies specific filter values, verifies compound filter behavior, tests column sorting, and clicks "Clear Filters" to restore the unfiltered log view.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Ingested Logs: 25+ entries across diverse paths (`/blog/guide`, `/klimalar`, `/pricing`, `/api/v1`), status codes (200, 404, 500), and platforms (ChatGPT, Claude, Perplexity).
- **Prerequisites**:
  - Server Logs tab active.

## 4. Gherkin Scenario

```gherkin
Feature: Edge Server Logs Multi-Dimensional Filtering & Sorting
  As an AI Search Analyst
  I want to query and filter raw crawler HTTP logs by path, status, and AI platform
  So that I can investigate crawler access patterns and identify indexing barriers

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/agentanalytics"
    And the user switches to the Server Logs tab "button.aa-tab-item[data-tab='logs']"
    And the logs toolbar ".aa-logs-toolbar" is rendered

  Scenario Outline: Filter server logs by path substring
    When the user types "<path_query>" into the search input "input[data-action-input='aa-log-search']"
    Then all displayed rows in the logs table should contain "<path_query>" in their path cell

    Examples:
      | path_query   |
      | /blog        |
      | /klimalar    |
      | /pricing     |

  Scenario Outline: Filter server logs using dropdown menus
    When the user opens the filter dropdown "<dropdown_trigger>"
    And the user selects option "<filter_option>"
    Then the logs table should only show rows matching "<filter_option>"

    Examples:
      | dropdown_trigger                                         | filter_option |
      | button.aa-dd-trigger[data-action='aa-toggle-log-filters']  | 200           |
      | button.aa-dd-trigger[data-action='aa-toggle-log-filters']  | 404           |
      | button.aa-dd-trigger[data-action='aa-toggle-log-platforms']| ChatGPT       |
      | button.aa-dd-trigger[data-action='aa-toggle-log-platforms']| Claude        |

  Scenario: Reset all filters to default full view
    Given active path, status, and platform filters are applied
    When the user clicks the clear button "button[data-action='aa-clear-log-filters']"
    Then the search input should be cleared
    And the status filter should reset to "all"
    And the platform filter should reset to "all"
    And the logs table should display the full unfiltered dataset
```

## 5. Visual Checks
- **Search Input**: Clean text input with magnifying glass icon.
- **Dropdown Menus**: `.aa-dd-menu` floats cleanly below trigger buttons with backdrop protection.
- **Active Pills**: Applied filter chips render with distinct active highlight.

## 6. Data and Network Checks
- **Filter State Properties**:
  ```javascript
  const state = window.AgentAnalyticsState;
  assert.strictEqual(state.logStatusFilter, 'all');
  assert.strictEqual(state.logPlatformFilter, 'all');
  assert.strictEqual(state.logPathSearch, '');
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-server-logs-filtering-and-search/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-09-path-filtered.png`
     - `/tmp/ego-shots/tc-aa-09-status-dropdown.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-09-*.png ./01-gherkin-result-case-server-logs-filtering-and-search/
     ```
