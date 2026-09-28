# Test Case: Frequency Granularity Invariant (Daily vs Weekly)

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-11`
- **Purpose**: Verify that switching data frequency between Daily (`"daily"`) and Weekly (`"weekly"`) via the overview dropdown menu (`ovDD("freq")`) accurately aggregates historical intervals ($n = \max(2, \text{round}(\text{days} / 7))$), formats date tick labels cleanly across bilingual locales (TR/EN), and recalculates trend points without date overlap.

---

## 2. Tester Brief
The Overview Dashboard supports multiple aggregation granularities:
- **Daily**: Renders raw daily measurements.
- **Weekly**: Aggregates intervals into 7-day buckets, reducing tick clutter on extended ranges (e.g. 90D).
- Date label strings must adapt according to active language (e.g. `"Aug 28"` in English vs `"28 Ağu"` in Turkish).

The tester verifies that switching to Weekly granularity on a 90D timeframe produces between 10 and 15 aggregated date ticks, updates the dropdown trigger label, and formats axis dates without errors.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Dropdown Control**: `button[data-action="ov-dd"][data-dd="freq"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: Time Series Frequency Granularity Aggregation
  As a marketing strategist
  I want to switch between Daily and Weekly aggregation granularities
  So that I can smooth out daily fluctuations and observe broader week-over-week trends.

  Scenario Outline: Switching between Daily and Weekly frequency
    Given the user is on the Overview Dashboard
    When the user opens the frequency dropdown menu
    And the user selects the granularity option "<Granularity>"
    Then "state.ov.freq" should equal "<Granularity>"
    And the trend chart X-axis should render aggregated date intervals matching "<ExpectedTickRange>"
    And the date strings should adhere to the active language format

    Examples:
      | Granularity | ExpectedTickRange |
      | daily       | 4 to 30 ticks     |
      | weekly      | 10 to 15 ticks    |
```

---

## 5. Visual Checks
- **Dropdown Menu**: `.ov-dd-menu` containing Daily and Weekly items.
- **Tick Density**: Weekly mode shows visibly spaced, clean date labels without overlapping text.
- **Bilingual Formatting**: Respects Turkish vs English month abbreviations.

---

## 6. Data and Network Checks
- **Aggregation Invariant Assertion**:
  ```javascript
  const freqCheck = await js(String.raw`(() => {
    const origFreq = window.state?.ov?.freq || 'daily';
    
    // Set to weekly on 90D
    if (window.state && window.state.ov) {
      window.state.ov.freq = 'weekly';
      window.state.ov.range = '90d';
      window.rerender();
    }

    const p = (typeof profile === 'function') ? profile() : window.state?.activeProfileBundle;
    const axisLabels = typeof ovAxis === 'function' ? ovAxis(p) : [];
    const countOk = axisLabels.length >= 10 && axisLabels.length <= 15;

    // Restore
    if (window.state && window.state.ov) {
      window.state.ov.freq = origFreq;
      window.rerender();
    }

    return {
      axisLabelsCount: axisLabels.length,
      countOk,
      noError: !window.__lastError
    };
  })()`);
  if (!freqCheck.countOk || !freqCheck.noError) {
    throw new Error('Weekly aggregation produced unexpected tick count for 90D');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-frequency-granularity-aggregation/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of Daily and Weekly charts saved in result directory.
  - SCP sync from MacBook to host before final report logging.
