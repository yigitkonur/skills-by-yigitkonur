# Case 02: Known Crawler Classification & Traffic Share Distribution

## 1. Case ID and Purpose
- **Case ID**: `TC-AA-02`
- **Purpose**: Verify that the Agent Analytics engine accurately identifies and classifies ingested crawler request telemetry across all 6 registered AI bot signatures (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, Amazonbot, ByteSpider), computes proportional request shares, renders visual progress distribution bars, and identifies the dominant top bot crawler.

## 2. Tester Brief
The tester injects a multi-bot telemetry dataset containing varying proportions of recognized AI search agents and crawlers into `window.AgentAnalyticsState.logs`. The tester validates the Overview Cockpit cards ("Total Requests", "Bot Share", "Top Bot"), verifies that the Bot Distribution card renders progress bars proportional to request volumes, switches to the Bot Visits tab, and confirms that the Platforms table registers each bot with the correct platform identity and categorization.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Ingested Request Batch:
    - 40x `GPTBot/1.2` (OpenAI / ChatGPT)
    - 25x `ClaudeBot/1.0` (Anthropic / Claude)
    - 15x `PerplexityBot/1.0` (Perplexity)
    - 10x `Google-Extended` (Google / Gemini)
    - 6x `Amazonbot/0.1` (Amazon)
    - 4x `ByteSpider` (TikTok / ByteDance)
  - Total Crawler Requests: 100 requests (all HTTP 200)
- **Prerequisites**:
  - Application loaded at `[APP_URL]/#/[SLUG]/agentanalytics`.

## 4. Gherkin Scenario

```gherkin
Feature: AI Bot Crawler Telemetry Classification & Distribution
  As a Search Intelligence Analyst
  I want to monitor the exact distribution of autonomous AI crawlers
  So that I can identify which LLM retrieval engines are actively crawling my domain

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/agentanalytics"
    And 100 crawler log entries spanning 6 AI platforms are ingested into "window.AgentAnalyticsState.logs"
    And the Overview tab is active

  Scenario: Verify Macro Crawler Cockpit and Top Bot identification
    Then the Total Requests card ".aa-crawler-card[data-metric='total-requests']" should display "100"
    And the Bot Share card ".aa-crawler-card[data-metric='bot-share']" should display "100%"
    And the 200 OK Rate card ".aa-crawler-card[data-metric='200-ok-rate']" should display "100%"
    And the Top Bot card ".aa-crawler-card[data-metric='top-bot']" should display "GPTBot"

  Scenario Outline: Verify individual crawler classification and distribution progress bars
    Then the bot distribution list should contain item for "<bot_id>"
    And the item for "<bot_id>" should display label "<display_name>"
    And the item for "<bot_id>" should reflect request count "<expected_count>" and share "<expected_share>"
    And the progress bar fill ".aa-bot-dist-bar-fill" for "<bot_id>" should have proportional width

    Examples:
      | bot_id          | display_name     | expected_count | expected_share |
      | chatgpt         | GPTBot           | 40             | 40%            |
      | claudebot       | ClaudeBot        | 25             | 25%            |
      | perplexity      | PerplexityBot    | 15             | 15%            |
      | gemini          | Google-Extended  | 10             | 10%            |
      | amazonbot       | Amazonbot        | 6              | 6%             |
      | bytespider      | ByteSpider       | 4              | 4%             |

  Scenario Outline: Verify Bot Visits platform table mapping and categories
    When the user clicks the sub-tab "button.aa-tab-item[data-tab='bot-visits']"
    Then the Bot Platforms table should contain a row for platform "<platform_name>"
    And the row for "<platform_name>" should display category "<bot_category>"

    Examples:
      | platform_name   | bot_category            |
      | ChatGPT         | AI Assistant & Indexing |
      | Claude          | AI Search & Assistant   |
      | Perplexity      | AI Search & Assistant   |
      | Gemini          | AI Indexing & Training  |
      | Amazon          | AI Search & Assistant   |
      | TikTok/ByteDance| Social AI Crawler       |
```

## 5. Visual Checks
- **Cockpit Metrics**: Metric values render in clean monospaced font (`.aa-kpi-val.mono`).
- **Distribution Progress Bars**: `.aa-bot-dist-bar-fill` colors adhere to platform theme accents (e.g. green for ChatGPT, purple for Claude, teal for Perplexity).
- **Dominant Badge**: Top Bot card renders an "Active" or "Dominant" badge when share >= 40%.

## 6. Data and Network Checks
- **Synchronized State Assertions**:
  ```javascript
  const state = window.AgentAnalyticsState;
  assert.strictEqual(state.logs.length, 100);
  const dist = window.computeBotDistribution(state.logs);
  assert.strictEqual(dist['chatgpt'].count, 40);
  assert.strictEqual(dist['claudebot'].count, 25);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `01-gherkin-result-case-crawler-classification-distribution/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-aa-02-overview-distribution.png` (Overview bars)
     - `/tmp/ego-shots/tc-aa-02-bot-visits-table.png` (Platforms table)
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-aa-02-*.png ./01-gherkin-result-case-crawler-classification-distribution/
     ```
