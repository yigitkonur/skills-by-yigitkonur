# Case 12: Telemetry CSV Export & Live Workspace Provenance Boundary

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-12`
- **Purpose**: Verify the data provenance contract of edge telemetry log exporting, ensuring that in static/demo mode the CSV export button generates a correctly formatted `zeo-agent-analytics-logs.csv` file (including handling zero-visit empty states with a single valid header row without throwing `TypeError`), and that in live production mode (`aaIsLive() === true`), the demo export button is strictly omitted from the DOM and synthetic dispatches are completely inert.

## 2. Tester Brief
The tester evaluates log exporting under two environment modes:
1. Demo mode: With empty logs (`state.logs = []`), the tester clicks `button[data-action="aa-export-logs"]`, intercepts `window.downloadCSV`, and verifies that exactly 1 header row is exported. Next, with populated logs, the tester verifies that rows map accurately to the CSV schema.
2. Live mode: The tester configures the live data provider mode (`ZEO_DATA_PROVIDER.getMode() === 'live'`), navigates to Server Logs, asserts that the sample export button is absent from the DOM, and confirms that dispatching the action is completely inert.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Expected CSV Filename: `'zeo-agent-analytics-logs.csv'`
  - Required CSV Headers: `['Timestamp', 'Platform', 'BotType', 'UserAgent', 'Path', 'Status']`
- **Prerequisites**:
  - Server Logs tab active.

## 4. Gherkin Scenario

```gherkin
Feature: Telemetry CSV Export Contract & Live Boundary Enforcement
  As a Data Compliance Auditor
  I want telemetry CSV exports to accurately reflect ingested logs in demo mode
  And I want sample demo export buttons strictly hidden in live customer workspaces

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/agentanalytics"
    And the user switches to the Server Logs tab "button.aa-tab-item[data-tab='logs']"

  Scenario: Export zero-visit telemetry logs in demo mode
    Given the data provider is running in "demo" mode
    And the telemetry log stream contains 0 entries
    When the user clicks the export button "button[data-action='aa-export-logs']"
    Then the CSV download handler "window.downloadCSV" should be invoked
    And the downloaded filename should be "zeo-agent-analytics-logs.csv"
    And the exported payload should contain exactly 1 row corresponding to the header schema:
      | Timestamp | Platform | BotType | UserAgent | Path | Status |

  Scenario: Export populated telemetry logs in demo mode
    Given the data provider is running in "demo" mode
    And the telemetry log stream contains 15 crawler records
    When the user clicks the export button "button[data-action='aa-export-logs']"
    Then the exported payload should contain 16 rows (1 header row plus 15 data rows)
    And no field values should be undefined or null

  Scenario: Enforce live workspace boundary and omit sample export
    Given the data provider is running in "live" mode with active database streaming
    When the Server Logs tab is rendered
    Then the sample export button "button[data-action='aa-export-logs']" should not exist in the DOM
    When a synthetic "aa-export-logs" action event is dispatched directly to the document
    Then the action should be inert
    And no fake success toast notification should be displayed
```

## 5. Visual Checks
- **Demo Mode**: Export button renders in logs toolbar with download icon.
- **Live Mode**: Export button is completely absent; toolbar maintains clean spacing without awkward empty gaps.

## 6. Data and Network Checks
- **Export Hook Interception**:
  ```javascript
  let lastCsv = null;
  window.downloadCSV = (filename, rows) => { lastCsv = { filename, rows }; };
  document.querySelector("button[data-action='aa-export-logs']").click();
  assert.strictEqual(lastCsv.filename, 'zeo-agent-analytics-logs.csv');
  assert.strictEqual(lastCsv.rows[0][0], 'Timestamp');
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-telemetry-export-provenance-boundary/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-12-demo-export.png`
     - `/tmp/ego-shots/tc-aa-12-live-no-export.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-12-*.png ./01-gherkin-result-case-telemetry-export-provenance-boundary/
     ```
