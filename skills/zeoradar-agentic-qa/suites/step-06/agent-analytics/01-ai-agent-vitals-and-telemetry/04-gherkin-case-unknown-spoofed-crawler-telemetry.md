# Case 04: Unknown, Spoofed & Empty Crawler Telemetry Handling

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-04`
- **Purpose**: Verify that the Agent Analytics ingestion pipeline and UI components defend against malformed, spoofed, empty, or unrecognized User-Agent strings, categorizing them defensively under `id = 'other'` without corrupting catalog bot metrics, displaying exact UA strings in the User-Agents tab, safely rendering fallback `"Unknown"` labels for blank entries, and gracefully providing generic fallback structures (`fallbackBot`) if deep-dive views are triggered on unregistered bot identifiers.

## 2. Tester Brief
The tester injects edge logs with abnormal or adversary User-Agents into the active telemetry state: an unregistered custom scraper (`CustomScraper/2.1`), an empty string UA, and a spoofed bot header. The tester switches between the Platforms and User-Agents views on the Bot Visits tab, verifies that registered bot counts remain uncorrupted while unknown entries appear under the `other` category, tests that empty strings do not throw JavaScript `TypeError`s, and invokes a deep-dive view using an unregistered ID to verify the resilient `fallbackBot` canvas.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Injected Telemetry Records:
    1. Unregistered AI Scraper: `bot: null, ua: "CustomScraper/2.1 (+https://ai-research.example.com)", platform: "unknown-engine"`
    2. Spoofed Header: `bot: null, ua: "Mozilla/5.0 (compatible; FakeBot/1.0)", platform: "spoofed"`
    3. Blank UA Entry: `bot: "", ua: "", platform: ""`
- **Prerequisites**:
  - Application loaded on Agent Analytics view.

## 4. Gherkin Scenario

```gherkin
Feature: Defensive Handling of Unknown, Spoofed and Empty Bot Telemetry
  As an Application Resilience Engineer
  I want edge telemetry ingestion to defensively isolate unrecognized and malformed crawlers
  So that bad actor scripts or custom research bots cannot crash the UI or corrupt standard metrics

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/agentanalytics"
    And the user switches to the Bot Visits tab "button.aa-tab-item[data-tab='bot-visits']"

  Scenario Outline: Ingest abnormal crawler telemetry and verify defensive categorization
    When an edge log entry with user agent "<input_ua>" and bot field "<input_bot>" is ingested
    Then the telemetry processor should assign the bot identifier "other"
    And the assigned platform category should be "General Web Scraper" or "General"
    And the registered catalog bot metrics for "GPTBot" and "ClaudeBot" should remain unpolluted

    Examples:
      | input_ua                                              | input_bot |
      | CustomScraper/2.1 (+https://ai-research.example.com)  | null      |
      | Mozilla/5.0 (compatible; FakeBot/1.0)                 | null      |
      |                                                       |           |

  Scenario: Verify User-Agents segmented table view displays uncurated strings
    Given abnormal crawler entries have been ingested into the active log stream
    When the user clicks the segmented view button "button[data-action='aa-bot-view'][data-v='user-agents']"
    Then the table should render the full user agent string "CustomScraper/2.1 (+https://ai-research.example.com)"
    And the row should display a non-zero visit count and a valid calculated share percentage
    And the entry with an empty user agent should render the fallback label "Unknown" instead of blank text

  Scenario: Verify resilient deep-dive fallback for unregistered bot identifier
    When the user triggers deep-dive navigation for an unregistered bot "data-id='unregistered_crawler_99'"
    Then the view branch ".aa-bot-deepdive-branch" should render without throwing runtime exceptions
    And the view title should display the fallback name "AI Crawler"
    And the platform category should display "General"
    And the KPI trio should display "0" humans referred and "–" last visit date
    And the canvas should remain interactive allowing back navigation via "< All Bots"
```

## 5. Visual Checks
- **User-Agents Table**: Monospaced user-agent strings wrap cleanly without breaking table borders (`.tbl.aa-tbl`).
- **Empty UA Fallback**: Blank user agent displays `"Unknown"` in muted gray italic styling.
- **Deep-Dive Fallback**: Header renders generic bot badge; trend SVG renders flat baseline curve without SVG syntax errors (`NaN` coordinates).

## 6. Data and Network Checks
- **Defensive State Properties**:
  ```javascript
  const state = window.AgentAnalyticsState;
  const unknownItem = state.logs.find(x => x.id === 'log_unknown_test');
  assert.ok(unknownItem, 'Log record should exist in state');
  // Trigger unregistered deep-dive
  state.selectedBotDetail = 'unregistered_crawler_99';
  window.renderAgentAnalyticsPage(state);
  const deepDiveText = document.querySelector('.aa-bot-deepdive-branch').textContent;
  assert.ok(deepDiveText.includes('AI Crawler'), 'Fallback AI Crawler text must be rendered');
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-unknown-spoofed-crawler-telemetry/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-04-unknown-ua-table.png`
     - `/tmp/ego-shots/tc-aa-04-fallback-deepdive.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-04-*.png ./01-gherkin-result-case-unknown-spoofed-crawler-telemetry/
     ```
