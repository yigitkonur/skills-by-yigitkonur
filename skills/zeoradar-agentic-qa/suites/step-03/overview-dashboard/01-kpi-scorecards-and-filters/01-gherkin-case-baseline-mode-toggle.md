# Test Case: Single-Run Baseline Guard & Multi-Run Toggle

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-08`
- **Purpose**: Verify that workspaces with a single published run honestly display `"Baseline established (1 run)"` and `.ov-demo-badge` rather than fabricating artificial change deltas, and verify that multi-run workspaces support toggling baseline comparison mode between `"prev"` and `"baseline90d"` via `.ov-baseline-tag`.

---

## 2. Tester Brief
A common flaw in analytics platforms is displaying an artificial positive change (e.g. `+0.0% vs prev`) when only one run has ever executed.
Zeo Geo-Radar enforces strict baseline honesty:
1. When `ovPublishedRunCount(p) === 1`:
   - Delta text displays `"Baseline established (1 run)"` / `"Temel oluşturuldu (1 koşu)"`.
   - Tooltip explains: `"Baseline established from initial published run. Change figures require at least two runs."`.
   - Synthetic trend badge `.ov-demo-badge` informs user that the historical curve is simulated from the latest snapshot.
2. When multi-run data exists or baseline tag is clicked:
   - Clicking `.ov-baseline-tag[data-action="ov-toggle-baseline"]` cleanly alternates `state.ov.baselineMode` between `"prev"` ("vs Previous Period ⇄") and `"baseline90d"` ("vs 90D Baseline ⇄").

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Profile Data**: Evaluated single-run or multi-run profile bundle.

---

## 4. Gherkin Scenario

```gherkin
Feature: Baseline Honesty and Comparison Mode Switching
  As a product auditor
  I want single-run workspaces to clearly indicate baseline establishment
  And multi-run workspaces to allow toggling comparison baselines
  So that users are never misled by fabricated or ambiguous delta statistics.

  Scenario: Single-run baseline indicator and synthetic disclaimer
    Given the user is on the Overview Dashboard of a brand with a single published run
    Then the delta indicator ".ov-kpi-delta" should contain "Baseline established (1 run)" or its localized equivalent
    And the disclaimer badge ".ov-demo-badge" should be visible in the hero card
    And the disclaimer badge tooltip should state "Simulated series derived from the latest snapshot"

  Scenario Outline: Toggling baseline comparison mode
    Given the user is on the Overview Dashboard
    When the user clicks the baseline toggle tag ".ov-baseline-tag"
    Then "state.ov.baselineMode" should switch to "<TargetMode>"
    And the tag text should display "<ExpectedTagLabel>"

    Examples:
      | TargetMode   | ExpectedTagLabel      |
      | baseline90d  | vs 90D Baseline ⇄     |
      | prev         | vs Previous Period ⇄  |
```

---

## 5. Visual Checks
- **Delta Indicator**: `.ov-kpi-delta` containing baseline or directional delta (`▲ +X.X%` or `▼ X.X%`).
- **Baseline Tag**: `.ov-baseline-tag[data-action="ov-toggle-baseline"]` with bidirectional arrow symbol `⇄`.
- **Disclaimer Badge**: `.ov-demo-badge` styled in subtle muted color.

---

## 6. Data and Network Checks
- **DOM & State Assertion**:
  ```javascript
  const baselineCheck = await js(String.raw`(() => {
    const p = (typeof profile === 'function') ? profile() : window.state?.activeProfileBundle;
    const runCount = typeof ovPublishedRunCount === 'function' ? ovPublishedRunCount(p) : 1;
    const deltaText = document.querySelector('.ov-kpi-delta')?.innerText?.trim() || '';
    const hasDemoBadge = !!document.querySelector('.ov-demo-badge');
    const tag = document.querySelector('[data-action="ov-toggle-baseline"]');

    let toggleWorking = false;
    if (tag) {
      const mode0 = window.state?.ov?.baselineMode || 'prev';
      tag.click();
      const mode1 = window.state?.ov?.baselineMode;
      toggleWorking = (mode0 !== mode1);
      tag.click(); // restore
    }

    return { runCount, deltaText, hasDemoBadge, toggleWorking, noError: !window.__lastError };
  })()`);
  if (baselineCheck.runCount === 1) {
    if (!baselineCheck.deltaText.includes('Baseline') && !baselineCheck.deltaText.includes('Temel')) {
      throw new Error('Single-run baseline indicator missing or misleading');
    }
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-baseline-mode-toggle/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of baseline indicator and toggled baseline mode saved in result directory.
  - Remote artifacts retrieved via SCP before final test report assembly.
