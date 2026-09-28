# Case 01: Initial Render, Unconnected Stream State & Hero Integration Banner

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-01`
- **Purpose**: Verify that when the application loads without an active edge crawler telemetry stream (`state.logs = []`), the Agent Analytics module cleanly renders a disconnected connection indicator, displays the informative Hero Integration Banner with actionable setup buttons, presents honest zero/dash states across the 4 cockpit KPI cards, and renders an empty state explanation in the Crawled URLs table without UI freezing or uncaught exceptions.

## 2. Tester Brief
The tester or AI agent navigates to the Agent Analytics route (`/#/app/:slug/agentanalytics`) for a project that has not yet configured edge log streaming (e.g. Cloudflare Logpush or Dokploy Traefik proxy). The tester observes the global header connection status, confirms the absence of green pulsing indicators, validates the guidance in the Hero Integration Banner, verifies that the 4 KPI cards display `0` or `–` rather than corrupted placeholders or NaN, and verifies that clicking the setup triggers inside the hero banner launches the setup wizard and logs integration console.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]` (e.g. `daikin.com.tr`)
  - Route URL: `[APP_URL]/#/[SLUG]/agentanalytics`
  - Telemetry State: `window.AgentAnalyticsState.logs = []`
- **Prerequisites**:
  - Live production deployment reachable at `https://zeoradar.endpoints.lol/`.
  - User session active in project context.

## 4. Gherkin Scenario

```gherkin
Feature: Agent Analytics Initial Render & Disconnected Stream Handling
  As a SEO and AI Infrastructure Engineer
  I want to clearly see whether edge crawler telemetry is streaming
  So that I know when integration setup is required before analyzing bot visits

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/agentanalytics"
    And the application has loaded the Agent Analytics container ".aa-container"
    And the edge crawler telemetry stream contains 0 ingested records

  Scenario: Verify honest disconnected status and Hero Integration Banner
    Then the header should display the active domain badge for "[DOMAIN]"
    And the connection indicator ".aa-connection-indicator" should have class "aa-disconnected"
    And the connection indicator should not contain a pulsing online dot ".aa-status-dot.online.pulse"
    And the active tab should default to "overview"
    And the overview section should display the Hero Integration Banner ".aa-hero-banner"
    And the Hero Banner should contain an "Open Server Logs" button and a "Setup Wizard" button
    And the crawler overview cockpit should display the following KPI card values:
      | Metric Card Selector                        | Expected Value |
      | .aa-crawler-card[data-metric="total-requests"] | 0              |
      | .aa-crawler-card[data-metric="bot-share"]      | –              |
      | .aa-crawler-card[data-metric="200-ok-rate"]    | –              |
      | .aa-crawler-card[data-metric="top-bot"]        | –              |
    And the Crawled URLs Breakdown table should render the empty message:
      """
      No crawled URLs recorded yet. Ingest crawler logs to populate this table.
      """

  Scenario Outline: Navigate to integration setup via Hero Banner action buttons
    When the user clicks the hero action button "<button_selector>"
    Then the application should perform the navigation action "<expected_action>"

    Examples:
      | button_selector                                       | expected_action                         |
      | .aa-hero-banner button[data-action="aa-tab"][data-tab="logs"] | switch to active tab "logs"             |
      | .aa-hero-banner button[data-action="aa-open-wizard"]          | open setup wizard modal ".aa-wizard"    |
```

## 5. Visual Checks
- **Header Badge**: `.aa-domain-badge` renders with clear typography displaying `[DOMAIN]`.
- **Status Dot**: Connection dot renders in neutral muted gray without CSS animation `.pulse`.
- **Hero Banner**: `.aa-hero-banner` is clearly styled with border, icon, and actionable call-to-action buttons.
- **KPI Cockpit**: Card labels "Total Requests", "Bot Share", "200 OK Rate", and "Top Bot" render with clear metric typography; no broken card layouts.
- **Empty State Typography**: Crawled URLs table empty notice is centered with muted ink styling (`.dim`).

## 6. Data and Network Checks
- **State Property Assertions**:
  ```javascript
  assert.strictEqual(window.AgentAnalyticsState.activeTab, 'overview');
  assert.strictEqual(window.AgentAnalyticsState.logs.length, 0);
  assert.strictEqual(document.querySelectorAll('.aa-status-dot.online.pulse').length, 0);
  ```
- **Console Log Hygiene**: Zero uncaught `TypeError` or `ReferenceError` during empty state rendering.

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-initial-render-unconnected-hero/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Full-page screenshot captured at `/tmp/ego-shots/tc-aa-01-hero-disconnected.png`.
  3. Transferred locally via:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-01-hero-disconnected.png ./01-gherkin-result-case-initial-render-unconnected-hero/
     ```
  4. Execution summary documented in matching result directory `REPORT.md`.
