# Case 06: Core Web Vitals Audit Runner Execution & Thresholds

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-06`
- **Purpose**: Verify that the Core Web Vitals synthetic audit runner (`run-vitals-audit`) executes successfully across both `mobile` and `desktop` strategies, updates the audit button to a disabled analyzing spinner state while in flight, populates the Lighthouse performance score badge (`0–100`), and maps all 6 Core Web Vitals (FCP, LCP, TTI, Speed Index, TBT, CLS) to correct qualitative health badges (`good`, `warning`, `bad`) based on standardized latency thresholds.

## 2. Tester Brief
The tester switches to the Pages tab (`data-tab="pages"`), verifies the default `mobile` strategy, tests toggling to `desktop`, specifies a target URL endpoint (e.g. `https://[DOMAIN]/products`), and clicks the "Run Audit" button. The tester asserts that the button enters the active loading state, waits for the response from `ZEO_DATA_PROVIDER.dispatchCommand('run-vitals-audit')`, and verifies that the Lighthouse score badge appears with the proper color-coded classification along with all 6 individual vital metric cards.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Target URL: `https://[DOMAIN]/products`
  - Strategies: `mobile`, `desktop`
  - Metric Threshold Standards:
    - FCP: `<= 1800ms` (Good), `<= 3000ms` (Needs Improvement), `> 3000ms` (Poor)
    - LCP: `<= 2500ms` (Good), `<= 4000ms` (Needs Improvement), `> 4000ms` (Poor)
    - TTI: `<= 3800ms` (Good), `<= 7300ms` (Needs Improvement), `> 7300ms` (Poor)
    - Speed Index: `<= 3400ms` (Good), `<= 5800ms` (Needs Improvement), `> 5800ms` (Poor)
    - TBT: `<= 200ms` (Good), `<= 600ms` (Needs Improvement), `> 600ms` (Poor)
    - CLS: `<= 0.100` (Good), `<= 0.250` (Needs Improvement), `> 0.250` (Poor)
- **Prerequisites**:
  - Application loaded on Pages tab.

## 4. Gherkin Scenario

```gherkin
Feature: Synthetic Core Web Vitals Audit Runner
  As a Technical Web Performance Specialist
  I want to run synthetic Core Web Vitals audits against key landing pages
  So that I can optimize mobile and desktop page speeds for AI crawlers and human visitors

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/agentanalytics"
    And the user switches to the Pages tab "button.aa-tab-item[data-tab='pages']"
    And the Web Vitals section ".aa-card.aa-pad" is displayed

  Scenario Outline: Execute Web Vitals audit across emulation strategies
    Given the audit strategy is set to "<audit_strategy>"
    When the user enters target URL "https://[DOMAIN]/products" into "input[data-action-input='aa-vitals-url']"
    And the user clicks the Run Audit button "button[data-action='aa-run-vitals']"
    Then the Run Audit button should display disabled loading text "Analyzing..."
    And the command "run-vitals-audit" should be dispatched with strategy "<audit_strategy>"
    When the audit command resolves with a successful performance envelope
    Then the loading spinner should dismiss
    And the performance score badge ".aa-vitals-score-badge" should display an integer between 0 and 100
    And the audited timestamp ".aa-subdim" should display a recent time

    Examples:
      | audit_strategy |
      | mobile         |
      | desktop        |

  Scenario Outline: Verify Core Web Vitals metric thresholds and qualitative health pills
    Given an audit has resolved with measured value "<measured_value>" for metric "<metric_key>"
    Then the metric card for "<metric_key>" should display formatted value "<formatted_display>"
    And the metric health pill should reflect tone "<expected_health>"

    Examples:
      | metric_key  | measured_value | formatted_display | expected_health |
      | fcp         | 1450           | 1.45s             | good            |
      | lcp         | 2250           | 2.25s             | good            |
      | tti         | 2750           | 2.75s             | good            |
      | speedIndex  | 1880           | 1.88s             | good            |
      | tbt         | 120            | 120ms             | good            |
      | cls         | 0.035          | 0.035             | good            |
      | lcp         | 3400           | 3.40s             | warning         |
      | lcp         | 4500           | 4.50s             | bad             |
      | cls         | 0.280          | 0.280             | bad             |
```

## 5. Visual Checks
- **Score Badge**: High score (`>= 90`) renders with emerald background; mid score (`50-89`) amber; low score (`< 50`) ruby.
- **Metric Cards Grid**: 6 distinct cards in responsive CSS grid (`.aa-vitals-grid`).
- **Health Pills**: `.aa-pill.good`, `.aa-pill.warning`, and `.aa-pill.bad` badges render with consistent padding, borders, and typography.

## 6. Data and Network Checks
- **Command Dispatch Payload**:
  ```javascript
  // Intercepted ZEO_DATA_PROVIDER dispatch:
  assert.strictEqual(lastCommand.cmd, 'run-vitals-audit');
  assert.strictEqual(lastCommand.payload.url, 'https://[DOMAIN]/products');
  assert.ok(['mobile', 'desktop'].includes(lastCommand.payload.strategy));
  ```
- **State Hydration**: `window.AgentAnalyticsState.vitalsData.metrics` is populated with all 6 keys.

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-vitals-runner-core-metrics-audit/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-06-vitals-loading.png`
     - `/tmp/ego-shots/tc-aa-06-vitals-completed.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-06-*.png ./01-gherkin-result-case-vitals-runner-core-metrics-audit/
     ```
