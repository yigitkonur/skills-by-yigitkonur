# Case 07: Vitals Runner Failure & Error Code Handling

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-07`
- **Purpose**: Verify that when the Web Vitals audit runner encounters execution rejections, validation failures (e.g. malformed or non-HTTP URLs), network timeouts, rate limit caps, or origin server 502 errors, the application immediately unwinds the `webVitalsLoading` state, re-enables the Run Audit button for user retry, surfaces a controlled localized error toast notification, and preserves previously recorded metrics without rendering `NaN` or crashing the interface.

## 2. Tester Brief
The tester targets the Web Vitals runner on the Pages tab, enters an invalid or unreachable target URL (e.g. `invalid-domain`), and triggers the audit. The tester simulates or intercepts `ZEO_DATA_PROVIDER.dispatchCommand('run-vitals-audit')` returning error envelopes (`validation_failed`, `unreachable`, `rate_limited`, or a rejected promise). The tester verifies that the loading spinner clears immediately, the audit button is re-enabled, the error toast appears with clear diagnostic text, and prior vitals measurements remain intact.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Error Scenarios:
    - Code `validation_failed`: `"Target URL is unreachable or returned HTTP 502"`
    - Code `rate_limited`: `"Rate limit exceeded for synthetic audits"`
    - Code `unreachable`: `"DNS resolution failed for target host"`
    - Network Error: Rejected promise with `"Failed to fetch"`
- **Prerequisites**:
  - Application loaded on Pages tab.

## 4. Gherkin Scenario

```gherkin
Feature: Web Vitals Runner Error Resilience & Loading Lock Unwind
  As a Systems Quality Engineer
  I want the synthetic vitals runner to fail gracefully when URLs are invalid or unreachable
  So that users are never trapped in an endless loading spinner and can retry without refreshing

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/agentanalytics"
    And the user switches to the Pages tab "button.aa-tab-item[data-tab='pages']"

  Scenario Outline: Handle vitals audit command failures gracefully
    Given the user enters an invalid URL "invalid-url-target"
    When the user clicks the Run Audit button "button[data-action='aa-run-vitals']"
    And the backend command rejects with error code "<error_code>" and message "<error_message>"
    Then the loading flag "window.AgentAnalyticsState.webVitalsLoading" should become false
    And the Run Audit button should be re-enabled for user interaction
    And an error toast notification should appear containing text "<error_message>"
    And the vitals metric grid should preserve existing values or clean placeholder dashes "–"
    And the vitals metric cards should not render "NaN"

    Examples:
      | error_code        | error_message                                        |
      | validation_failed | Target URL is unreachable or returned HTTP 502       |
      | rate_limited      | Exceeded project synthetic audit quota               |
      | unreachable       | DNS resolution failed or origin timed out            |
      | network_error     | Failed to fetch from edge provider                   |

  Scenario: Retry audit successfully after initial failure
    Given a previous audit attempt failed with error "validation_failed"
    When the user enters a valid target URL "https://[DOMAIN]/valid-page"
    And the user clicks the re-enabled Run Audit button
    Then the audit should dispatch cleanly with the new URL
```

## 5. Visual Checks
- **Button State**: Returns from disabled *"Analyzing..."* with spinner to enabled *"Run Audit"* with sparkle icon.
- **Toast Styling**: Toast notification displays with error style (`.toast.error` or red accent).
- **Metric Grid Stability**: No `NaN`, `null`, or undefined tokens visible in `.aa-vitals-val`.

## 6. Data and Network Checks
- **Lock Release Assertions**:
  ```javascript
  assert.strictEqual(window.AgentAnalyticsState.webVitalsLoading, false);
  const btn = document.querySelector("button[data-action='aa-run-vitals']");
  assert.strictEqual(btn.disabled, false);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-vitals-runner-failure-resilience/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-07-error-toast.png`
     - `/tmp/ego-shots/tc-aa-07-re-enabled-button.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-07-*.png ./01-gherkin-result-case-vitals-runner-failure-resilience/
     ```
