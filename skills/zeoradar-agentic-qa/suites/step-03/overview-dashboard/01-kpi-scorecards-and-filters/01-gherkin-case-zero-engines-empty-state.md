# Test Case: Zero Engines Deselection & Empty State Invariant

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-KPI-06`
- **Purpose**: Verify that deselecting all answer engines (`state.platforms = new Set()`) safely triggers the empty state boundary, prevents division-by-zero errors or `NaN` outputs in KPI calculations (`visScore`, `shareOfVoice`), renders the skeleton placeholder `.ov-skeleton-wrap`, and displays the global reset trigger `.freset`.

---

## 2. Tester Brief
An adversarial edge condition occurs when a user unchecks every answer engine in the platforms filter. This reduces filtered answers to an empty array (`[]`).
If mathematical calculations fail to guard against empty sets, `0 / 0` can produce `NaN%` or trigger unhandled runtime exceptions.

The tester verifies that:
1. When all platforms are deselected, all KPI cards display `"–"` instead of `NaN` or `Infinity`.
2. Main hero KPI value renders `– <i class="info-ic">ⓘ</i>` with informative empty state tooltip.
3. Delta indicator displays `"No data yet"` / `"Henüz veri yok"`.
4. Chart area displays `.ov-kpi-chart.ov-skeleton-wrap` with call-to-action `"Click 'Run Now'..."`.
5. Global filter reset button `.freset[data-action="reset-filters"]` is visible and functional.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Filter Mutation**: `state.platforms = new Set()`

---

## 4. Gherkin Scenario

```gherkin
Feature: Zero Engines Deselection and Empty State Protection
  As a quality engineer auditing adversarial edge cases
  I want the Overview Dashboard to withstand complete engine deselection
  So that mathematical formulas never output NaN or crash the interface.

  Scenario: Deselecting all engines and verifying empty state defenses
    Given the user is on the Overview Dashboard
    When all answer engines are deselected setting the active engines set to empty
    And the dashboard rerenders
    Then all KPI scorecards must display "–" without any "NaN" or "Infinity" text
    And the hero visibility card must render the skeleton placeholder ".ov-skeleton-wrap"
    And the delta indicator must display "No data yet" or its localized equivalent
    And the global reset button "[data-action='reset-filters']" must be visible in the filter bar
    When the user clicks the reset filters button
    Then the default dataset must be fully restored
    And the skeleton placeholder must be replaced with the normal trend chart
```

---

## 5. Visual Checks
- **KPI Values**: Cards display `"–"` with monospaced style.
- **Hero Card**: `.ov-kpi-chart.ov-skeleton-wrap` rendering empty state message.
- **Reset Button**: `.filterbar .freset[data-action="reset-filters"]` rendered with reset icon `↺`.

---

## 6. Data and Network Checks
- **Adversarial Assertion**:
  ```javascript
  const zeroTest = await js(String.raw`(() => {
    window.state.platforms = new Set();
    window.rerender();

    const vals = [...document.querySelectorAll('.aei-kpi-val, .ov-kpi-val')].map(c => c.innerText.trim());
    const hasNan = vals.some(v => v.includes('NaN') || v.includes('Infinity'));
    const skeletonPresent = !!document.querySelector('.ov-kpi-chart.ov-skeleton-wrap');
    const resetPresent = !!document.querySelector('[data-action="reset-filters"]');

    // Restore
    window.state.platforms = null;
    window.rerender();

    return { vals, hasNan, skeletonPresent, resetPresent, noError: !window.__lastError };
  })()`);
  if (zeroTest.hasNan) throw new Error('Invariant Violated: NaN displayed on zero engines');
  if (!zeroTest.skeletonPresent || !zeroTest.resetPresent || !zeroTest.noError) {
    throw new Error('Empty state skeleton or reset button missing on zero engines');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-zero-engines-empty-state/`
- **Execution Model**:
  - Executed via `ego-browser nodejs` on MacBook or Linux VM.
  - Screenshots of empty state and recovered state captured in result directory.
  - Remote artifacts copied via SCP before logging final test report.
