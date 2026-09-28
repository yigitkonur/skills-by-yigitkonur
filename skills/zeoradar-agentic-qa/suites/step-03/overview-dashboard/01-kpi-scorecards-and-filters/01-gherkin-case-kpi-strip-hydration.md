# Test Case: Core KPI Scorecards Initial Hydration & Values

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-01`
- **Purpose**: Verify that the Overview Dashboard correctly hydratess and calculates the 4 primary KPI scorecards: Overall Visibility Score (`visScore`), AI Share of Voice (`shareOfVoice`), Average Position / Category Rank (`avgPosition`/`ovBrandRank`), and Sentiment Health (`sentimentData`), adhering to number formatting and non-empty status for active brands.

---

## 2. Tester Brief
The Overview Dashboard features a top scorecard strip (`.aei-kpi-strip.ov-kpi-strip`) containing 4 analytical scorecards:
1. **Visibility Score**: Percent of evaluated answers where `[BRAND_NAME]` was mentioned.
2. **Share of Voice**: Brand's citation share relative to all recognized competitors.
3. **Avg Rank**: Category rank (e.g. `#1 of 5`) or decimal rank fallback (e.g. `1.2`).
4. **Sentiment**: Percentage of positive claims across answered prompts.

The tester must confirm that on initial load of an active workspace, all 4 cards load without errors, render formatted percentages or ranks (not raw floating decimals or `NaN`), and show valid labels in the selected language.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Active Workspace**: Authenticated session with an active profile bundle (e.g. `[DOMAIN] = "daikin.com.tr"`, `[COUNTRY] = "TR"`, `[LANGUAGE] = "tr"`)
- **Answer Set**: Non-empty answers set (`p.answers.length > 0`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Overview Dashboard Core KPI Scorecards
  As a marketing executive or SEO lead
  I want to view high-level AI search KPIs across all answer engines
  So that I can quickly assess brand visibility, market voice, ranking, and sentiment health.

  Scenario Outline: Initial hydration of core KPI scorecards
    Given the user is authenticated in Zeo Geo-Radar for "[DOMAIN]" in "[LANGUAGE]"
    And the current active tab is "overview"
    When the Overview dashboard finishes rendering
    Then exactly 4 KPI scorecards should be displayed in the ".aei-kpi-strip" container
    And the scorecard for "<Metric>" should display a valid non-empty value matching "<ValuePattern>"
    And no scorecard should display "NaN", "undefined", or uncaught error strings

    Examples:
      | Metric           | ValuePattern        |
      | Visibility Score | ^[0-9]{1,3}\.[0-9]% |
      | Share of Voice   | ^[0-9]{1,3}\.[0-9]% |
      | Avg Rank         | ^(#[0-9]+|[0-9]\.[0-9]|–) |
      | Sentiment        | ^([0-9]{1,3}\.[0-9]%|–)   |
```

---

## 5. Visual Checks
- **Scorecard Container**: `.aei-kpi-strip.ov-kpi-strip` renders with responsive CSS grid (`grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))`).
- **Metric Cards**: 4 cards with class `.card.aei-kpi-card.ov-kpi-card`.
- **Card Labels**: `.aei-kpi-label.ov-kpi-label` displaying localized titles (`"Visibility Score"` / `"Görünürlük Skoru"`, `"Share of Voice"` / `"Ses Payı"`, `"Avg Rank"` / `"Ortalama Sıralama"`, `"Sentiment"` / `"Duygu Durumu"`).
- **Metric Values**: `.aei-kpi-val.mono` formatted cleanly in monospaced font.

---

## 6. Data and Network Checks
- **DOM & State Verification**:
  ```javascript
  const kpiCheck = await js(String.raw`(() => {
    const cards = [...document.querySelectorAll('.aei-kpi-card, .ov-kpi-card')];
    const data = cards.map(c => ({
      label: c.querySelector('.aei-kpi-label, .ov-kpi-label')?.innerText?.trim(),
      val: c.querySelector('.aei-kpi-val, .ov-kpi-val')?.innerText?.trim()
    }));
    const hasNan = data.some(d => !d.val || d.val.includes('NaN') || d.val.includes('undefined'));
    return { count: cards.length, data, hasNan, noError: !window.__lastError };
  })()`);
  if (kpiCheck.count !== 4 || kpiCheck.hasNan || !kpiCheck.noError) {
    throw new Error('KPI hydration assertion failed');
  }
  ```
- **Console / Network**: Ensure 0 unhandled promise rejections or 5xx API failures during scorecard rendering.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-kpi-strip-hydration/`
- **Execution Model**:
  - Script is executed via `ego-browser nodejs` on a physical MacBook or local host.
  - Test runner executes full phase 1-5 lifecycle.
  - Screenshots are captured via `snapshotText` or native full-page capture into the result directory.
  - Remote MacBook artifacts are retrieved via SCP before compiling final QA reports.
