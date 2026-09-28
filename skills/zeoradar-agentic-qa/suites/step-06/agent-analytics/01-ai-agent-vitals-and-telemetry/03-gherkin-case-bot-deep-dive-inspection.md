# Case 03: Bot Deep-Dive Inspection & Trend Visualizations

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-03`
- **Purpose**: Verify that drilling into a specific bot crawler from the Bot Visits tab opens the dedicated Bot Deep-Dive View Branch (`renderBotDeepDiveViewBranch`), renders the KPI Trio (Humans Referred, Last Visit, Indexed Pages %), draws the 30-day Bot Visits Trend SVG and Crawl Intent Donut SVG, lists specific user-agent versions and indexed pages, and cleanly returns to the master bot list via the `< All Bots` back button without state pollution.

## 2. Tester Brief
The tester navigates to the Bot Visits tab (`data-tab="bot-visits"`), clicks the inspect action for a registered bot (e.g. `ChatGPT` / `chatgpt`), and verifies that the interface transitions into the dedicated deep-dive view. The tester verifies that the `< All Bots` back button is present, inspects the KPI Trio, validates that both SVG visualizations render valid geometry (`path`, `circle`), checks the indexed pages table, tests the "View in Logs" shortcut, and clicks `< All Bots` to verify that `selectedBotDetail` is cleared and the main platforms table is restored.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Target Bot ID: `chatgpt` (display name `GPTBot`)
- **Prerequisites**:
  - Application active on Bot Visits tab.
  - Active telemetry contains logs for `chatgpt`.

## 4. Gherkin Scenario

```gherkin
Feature: Bot Deep-Dive Inspector & Visualizations
  As a Technical SEO Specialist
  I want to inspect granular crawling patterns and referral metrics for a single AI agent
  So that I can understand how search intent translates to crawl frequency and human referral traffic

  Background:
    Given the user is on the Agent Analytics page at "[APP_URL]/#/[SLUG]/agentanalytics"
    And the user switches to the Bot Visits tab "button.aa-tab-item[data-tab='bot-visits']"
    And the bot platforms table is rendered

  Scenario: Drill into ChatGPT deep-dive view and verify KPI trio and SVGs
    When the user clicks the inspect button "button[data-action='aa-open-bot-detail'][data-id='chatgpt']"
    Then the view branch ".aa-bot-deepdive-branch" should become visible
    And the header should display the back navigation button "button[data-action='aa-close-bot-detail']" with text containing "< All Bots"
    And the deep-dive KPI trio ".aa-kpi-grid.aa-kpi-trio" should render:
      | KPI Metric       | Expected Indicator            |
      | Humans Referred  | Positive count with delta     |
      | Last Bot Visit   | Relative or formatted date    |
      | Pages Indexed    | Percentage with delta         |
    And the Bot Visits Trend SVG ".aa-svg-trend" should render SVG path elements
    And the Crawl Intent Donut SVG ".aa-svg-donut" should render donut path segments for Indexing and Search
    And the Specific User-Agents table should list active versions for "GPTBot"
    And the Indexed Pages table should display top crawled paths with frequency bars

  Scenario: Test navigation from Deep Dive to filtered Server Logs
    Given the user is viewing the deep-dive branch for "chatgpt"
    When the user clicks the shortcut button "button[data-action='aa-goto-logs'][data-plat='ChatGPT']"
    Then the active tab should switch to "logs"
    And the platform filter in the logs toolbar should be set to "ChatGPT"
    And the logs table should only display records associated with ChatGPT

  Scenario: Return from Deep Dive to master Platforms view
    Given the user is viewing the deep-dive branch for "chatgpt"
    When the user clicks the back button "button[data-action='aa-close-bot-detail']"
    Then the deep-dive branch ".aa-bot-deepdive-branch" should be unmounted
    And the master Bot Platforms table should be restored
    And "window.AgentAnalyticsState.selectedBotDetail" should be null
```

## 5. Visual Checks
- **Deep-Dive Header**: Clear breadcrumb styling with `< All Bots` button.
- **Trend Curve SVG**: `.aa-svg-trend` renders smooth multi-day lines with subtle gradient fills and coordinate dots.
- **Donut Chart SVG**: `.aa-svg-donut` renders two contrasting segment arcs representing Crawl vs Search intent.
- **Back Transition**: Instant transition without flashing or scroll jumping.

## 6. Data and Network Checks
- **State Properties**:
  ```javascript
  assert.strictEqual(window.AgentAnalyticsState.selectedBotDetail, 'chatgpt');
  // After clicking back button:
  assert.strictEqual(window.AgentAnalyticsState.selectedBotDetail, null);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-bot-deep-dive-inspection/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-03-deepdive-cockpit.png`
     - `/tmp/ego-shots/tc-aa-03-svg-charts.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-03-*.png ./01-gherkin-result-case-bot-deep-dive-inspection/
     ```
