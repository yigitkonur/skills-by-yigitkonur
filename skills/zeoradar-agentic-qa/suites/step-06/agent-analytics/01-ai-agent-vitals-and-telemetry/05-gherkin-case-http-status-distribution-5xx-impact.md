# Case 05: HTTP Status Distribution & 5xx Server Error Impact

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-05`
- **Purpose**: Verify that the Agent Analytics cockpit accurately reflects HTTP status code distributions, that crawler requests resulting in server errors (HTTP 500, 502, 503) or rate limits (429) correctly degrade the "200 OK Rate" KPI card and trigger warning/negative indicator styles (`.aa-pill.neg`), that paths experiencing errors render red error pills in the Crawled URLs table, and that the Server Logs tab supports filtering specifically for 5xx/4xx error events.

## 2. Tester Brief
The tester injects a batch of edge logs containing a mixture of successful HTTP 200 requests and critical server errors (e.g. 10x 200 OK, 3x 500 Internal Server Error, 2x 503 Service Unavailable). On the Overview tab, the tester checks that the 200 OK Rate KPI reflects `10 / 15 = 66.7%` (or rounded `67%`) and adopts a warning/negative visual state. The tester verifies that the Crawled URLs Breakdown flags error paths with negative pills (e.g. `GET 500`), then switches to the Server Logs tab to test filtering by HTTP status `500` and inspects the error drawer details.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Injected Telemetry Batch:
    - 10x HTTP 200 OK (ChatGPT, Claude, Perplexity)
    - 3x HTTP 500 Internal Server Error (ChatGPT hitting `/api/search`)
    - 2x HTTP 503 Service Unavailable (Claude hitting `/checkout`)
  - Total Requests: 15
- **Prerequisites**:
  - Application loaded on Overview tab.

## 4. Gherkin Scenario

```gherkin
Feature: HTTP Status Code Telemetry & Server Error Degradation
  As an Infrastructure Reliability Engineer
  I want AI crawler server errors to be surfaced immediately with precise rate impact
  So that origin capacity issues or upstream 5xx regressions affecting LLM indexing can be mitigated

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/agentanalytics"
    And a log batch with 10 successful 200 responses and 5 server errors (500, 503) is ingested

  Scenario: Verify 200 OK Rate degradation and negative KPI styling
    When the Overview tab is rendered
    Then the Total Requests card should display "15"
    And the 200 OK Rate card ".aa-crawler-card[data-metric='200-ok-rate']" should display "67%" or "66.7%"
    And the 200 OK Rate card should reflect a degraded or warning tone
    And the Crawled URLs Breakdown table should render negative badges ".aa-pill.neg.mono" for paths experiencing errors:
      | Path            | Expected Status Badge |
      | /api/search     | 500                   |
      | /checkout       | 503                   |

  Scenario Outline: Filter edge server logs by error status code
    Given the user switches to the Server Logs tab "button.aa-tab-item[data-tab='logs']"
    When the user opens the HTTP status filter dropdown "button.aa-dd-trigger[data-action='aa-toggle-log-filters']"
    And the user selects status code filter "<selected_status>"
    Then the Server Logs table should only display rows with status code "<selected_status>"
    And each visible row should render a negative status badge ".aa-pill.neg"

    Examples:
      | selected_status |
      | 500             |
      | 503             |

  Scenario: Inspect server error details in slide-over drawer
    Given the user is on the Server Logs tab filtered by status "500"
    When the user clicks the first error row "tr.clickable[data-action='aa-open-drawer']"
    Then the slide-over drawer ".zr-drawer-panel.aa-drawer" should slide into view
    And the drawer status pill should have class ".aa-pill.neg"
    And the drawer status pill should display "GET 500" or "POST 500"
    And the drawer should display client IP, host domain, and full bot user agent
```

## 5. Visual Checks
- **200 OK Rate Card**: Pill switches from healthy green (`.pos`) to warning amber/red (`.neg`).
- **Crawled URLs Table**: Server error rows highlight with subtle background tint and distinct `.aa-pill.neg.mono` text.
- **Drawer Error Header**: Prominent red status pill in drawer header.

## 6. Data and Network Checks
- **Rate Calculation Assertion**:
  ```javascript
  const state = window.AgentAnalyticsState;
  const total = state.logs.length;
  const count200 = state.logs.filter(x => x.status === 200).length;
  const expectedRate = Math.round((count200 / total) * 100);
  assert.strictEqual(expectedRate, 67);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-http-status-distribution-5xx-impact/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-05-overview-degraded-rate.png`
     - `/tmp/ego-shots/tc-aa-05-logs-500-filter.png`
     - `/tmp/ego-shots/tc-aa-05-drawer-500-error.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-05-*.png ./01-gherkin-result-case-http-status-distribution-5xx-impact/
     ```
