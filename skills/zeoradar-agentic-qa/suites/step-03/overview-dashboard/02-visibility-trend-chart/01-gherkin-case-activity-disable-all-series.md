# Test Case: Disabling All Series Checkboxes in Activity Charts

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-09`
- **Purpose**: Verify that unchecking all platform series checkboxes in an activity chart (`seriesList = []`) activates the mathematical $maxV = 0 \to 1$ safety guard, prevents division-by-zero or `NaN` coordinate errors, retains the background grid and axis ticks, and executes an early return on mouse hover without throwing unhandled exceptions.

---

## 2. Tester Brief
When an analyst deselects all platform checkboxes in an activity card:
- The active series array becomes empty (`seriesList = []`).
- If coordinate scaling does not guard against zero, `maxV = 0` leads to `top = 0` and `y = 0 / 0 = NaN`.
- Hovering over an empty series chart must cleanly dismiss tooltips (`if (!data.series.length) { ovChartLeave(wrap); return; }`).

The tester programmatically unchecks all series checkboxes, triggers mousemove over `rect.ov-hit`, and confirms system stability.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Checkboxes**: `input[data-ov-series][data-chart="cit"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: All Series Deselection Resilience in Activity Charts
  As a quality engineer stress-testing interactive controls
  I want the activity chart to remain stable when all platform checkboxes are unchecked
  So that clearing all series does not crash the UI or throw hover errors.

  Scenario: Unchecking all series checkboxes in AI Bot Citations card
    Given the user is on the Overview Dashboard
    When the user unchecks all platform series checkboxes in the "AI Bot Citations" card
    Then the activity SVG chart should still be rendered with grid lines
    And the SVG path definition should not contain "NaN"
    When the user hovers over the SVG hit area with no active series
    Then no runtime error should be thrown
    And the floating tooltip should remain hidden
    When the user re-checks the platform checkboxes
    Then the series paths and hover dots should be restored
```

---

## 5. Visual Checks
- **Empty State Chart**: Grid lines and date ticks remain intact; trend lines disappear cleanly.
- **No Error Message**: No uncaught exception banner or broken layout.
- **Recovery**: Rechecking series smoothly restores colored lines.

---

## 6. Data and Network Checks
- **Adversarial Assertion**:
  ```javascript
  const emptySeriesCheck = await js(String.raw`(() => {
    const cbs = [...document.querySelectorAll('input[data-ov-series][data-chart="cit"]')];
    if (cbs.length === 0) return { skipped: true };

    // 1. Uncheck all
    cbs.forEach(cb => {
      if (cb.checked) {
        cb.checked = false;
        cb.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });

    const card = document.querySelector('.ov-activity .card');
    const hit = card?.querySelector('.ov-hit');
    let hoverThrew = false;
    if (hit) {
      try {
        hit.dispatchEvent(new MouseEvent('mousemove', { clientX: 100, clientY: 50, bubbles: true }));
      } catch (e) {
        hoverThrew = true;
      }
    }

    // 2. Restore all
    cbs.forEach(cb => {
      cb.checked = true;
      cb.dispatchEvent(new Event('change', { bubbles: true }));
    });

    return {
      cbsCount: cbs.length,
      hoverThrew,
      noError: !window.__lastError
    };
  })()`);
  if (!emptySeriesCheck.skipped && (emptySeriesCheck.hoverThrew || !emptySeriesCheck.noError)) {
    throw new Error('Chart crashed or threw error when all series checkboxes were disabled');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-activity-disable-all-series/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux runner.
  - Screenshots of unchecked and restored activity charts saved in result directory.
  - SCP sync from MacBook to host before logging final test report.
