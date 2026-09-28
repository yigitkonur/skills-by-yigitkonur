# Test Case: Bar Chart Mode Engine-by-Engine Breakdown

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-03`
- **Purpose**: Verify that in Bar mode (`mode="bar"`), the chart renders an engine-by-engine breakdown (`ovKpiBars`) consisting of vertical bar sticks (`div.ov-bar-stick`), proportional height scaling ($h_{\text{px}} = \max(4, \text{round}(v / (\max(V) \times 1.15) \times 150))$), platform color tokens (`ovPlatToken`), and synchronized platform labels with icons (`div.ov-bar-names`).

---

## 2. Tester Brief
When switching to Bar mode, each generative AI platform (ChatGPT, Perplexity, Gemini, Claude, and Google AI Mode) is assigned a dedicated vertical column:
- Column container: `.ov-bar-col`
- Visibility percentage: `span.ov-bar-val.mono` (e.g. `82%`)
- Vertical bar stick: `div.ov-bar-stick` styled with inline `height: <hpx>px` and `background: var(<token>)`
- Platform name bar: `.ov-bar-names` containing platform icon (`platIcon`) and label.

The tester verifies that columns are rendered for all active engines, sticks reflect calculated visibility percentages proportionally, and platform brand colors are applied accurately.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Active Mode**: `state.overviewChartMode = "bar"`

---

## 4. Gherkin Scenario

```gherkin
Feature: Bar Chart Engine Breakdown
  As an organic search manager
  I want to compare brand visibility across generative search engines in a bar chart
  So that I can identify which engines favor our brand and which require optimization.

  Scenario Outline: Validating engine column in bar chart mode
    Given the user is on the Overview Dashboard in "bar" chart mode
    Then the bar container ".ov-bars" should be visible
    And the column for engine "<EngineName>" should exist in ".ov-bars"
    And if "<EngineName>" has measurement data, it should contain a vertical stick ".ov-bar-stick" with height >= 4 pixels
    And the platform name bar ".ov-bar-names" should display "<EngineName>" with its platform icon

    Examples:
      | EngineName      |
      | ChatGPT         |
      | Perplexity      |
      | Gemini          |
      | Claude          |
```

---

## 5. Visual Checks
- **Bar Columns**: `.ov-bars` flex layout with `.ov-bar-col` columns.
- **Bar Sticks**: `.ov-bar-stick` styled with engine-specific color tokens (e.g. green for ChatGPT, orange for Claude, purple for Perplexity).
- **Labels**: `.ov-bar-names` aligned directly underneath corresponding bar columns.

---

## 6. Data and Network Checks
- **DOM & Height Calculation Verification**:
  ```javascript
  const barCheck = await js(String.raw`(() => {
    const barBtn = document.querySelector('[data-action="toggle-overview-mode"][data-mode="bar"]');
    if (barBtn) barBtn.click();

    const cols = [...document.querySelectorAll('.ov-bar-col')];
    const sticks = [...document.querySelectorAll('.ov-bar-stick')];
    const names = [...document.querySelectorAll('.ov-bar-name')].map(n => n.innerText.trim());

    // Check stick heights are numeric and >= 4px
    const stickHeightsValid = sticks.every(s => {
      const h = parseFloat(s.style.height);
      return !isNaN(h) && h >= 4;
    });

    return {
      colCount: cols.length,
      stickCount: sticks.length,
      names,
      stickHeightsValid,
      noError: !window.__lastError
    };
  })()`);
  if (barCheck.colCount === 0 || !barCheck.stickHeightsValid || !barCheck.noError) {
    throw new Error('Bar mode engine breakdown assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-bar-mode-engine-breakdown/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of bar columns and names captured in result directory.
  - SCP sync from MacBook to host before final test report delivery.
