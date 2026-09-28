# Test Case: Website Activity Twin Charts Rendering

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-08`
- **Purpose**: Verify that the Overview Dashboard renders the dual Website Activity twin charts (`ovActivityCard`) for AI Bot Citations (`chart="cit"`) and AI Referral Visits (`chart="ref"`), accurately displaying platform series checkboxes with activity counts, interactive SVGs, and comparative toggle switches.

---

## 2. Tester Brief
Below the primary visibility card, the Overview Dashboard features two paired activity cards:
1. **AI Bot Citations**: Daily crawl and citation frequency parsed across bot user agents (GPTBot, ClaudeBot, PerplexityBot, etc.).
2. **AI Referral Visits**: Click-through referral traffic originating from generative AI platforms.

Each card hosts:
- Multi-engine filter checkboxes (`input[data-ov-series]`) with total counts `(N)`.
- Mini SVG line chart (`w: 340, h: 150`).
- Comparative toggle switch (`.ct-switch[data-action="ov-compare"]`).

The tester verifies that both cards render cleanly, reflect data counts, and allow interactive inspection.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Container**: `.ov-activity` present in Overview layout.

---

## 4. Gherkin Scenario

```gherkin
Feature: Website Activity Twin Charts
  As a digital analyst
  I want to track both AI bot crawl activity and AI search referral traffic
  So that I can correlate LLM crawling frequency with actual referral visits to our site.

  Scenario Outline: Validating twin activity cards rendering
    Given the user is on the Overview Dashboard
    Then the activity card for "<ChartTitle>" should be displayed in ".ov-activity"
    And the card should contain series checkboxes for major AI platforms
    And the platform checkbox "<PlatformName>" should display a numeric citation or visit count
    And the card should render an interactive SVG chart "svg.ov-chart"
    And the card should include a comparative switch ".ct-switch[data-chart='<ChartKey>']"

    Examples:
      | ChartTitle          | ChartKey | PlatformName |
      | AI Bot Citations    | cit      | ChatGPT      |
      | AI Referral Visits  | ref      | Perplexity   |
```

---

## 5. Visual Checks
- **Twin Cards**: Dual-column layout inside `.ov-activity`.
- **Checkboxes**: `.ov-cb` with platform icons, labels, and monospaced count badge `.ov-cb-n`.
- **Mini SVG**: Responsive SVG curves rendered with crisp styling tokens.

---

## 6. Data and Network Checks
- **DOM Verification**:
  ```javascript
  const activityCheck = await js(String.raw`(() => {
    const cards = [...document.querySelectorAll('.activity-chart-card, .ov-activity .card')];
    const cbsCit = document.querySelectorAll('input[data-ov-series][data-chart="cit"]');
    const cbsRef = document.querySelectorAll('input[data-ov-series][data-chart="ref"]');
    const svgs = document.querySelectorAll('.ov-activity svg.ov-chart');

    return {
      cardsCount: cards.length,
      citCheckboxes: cbsCit.length,
      refCheckboxes: cbsRef.length,
      svgCount: svgs.length,
      noError: !window.__lastError
    };
  })()`);
  if (activityCheck.citCheckboxes === 0 || activityCheck.refCheckboxes === 0 || activityCheck.svgCount < 2) {
    throw new Error('Website activity twin charts assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-activity-twin-charts-rendering/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of AI Bot Citations and AI Referral Visits saved in result directory.
  - SCP sync from MacBook to host before final report logging.
