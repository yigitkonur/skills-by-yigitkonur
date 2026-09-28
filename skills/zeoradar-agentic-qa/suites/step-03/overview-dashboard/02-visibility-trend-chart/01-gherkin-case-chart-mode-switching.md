# Test Case: Line vs Bar Mode Segmented Switching

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-02`
- **Purpose**: Verify that toggling the chart mode segmented controls (`button[data-action="toggle-overview-mode"]`) cleanly switches between Line (`mode="line"`) and Bar (`mode="bar"`) visualizations, accurately updates the active CSS class `.black`, mutates `state.overviewChartMode`, and properly unmounts/mounts the respective chart containers.

---

## 2. Tester Brief
The Overview Dashboard hero card provides a segmented mode switcher:
- **Line Mode** (`data-mode="line"`): Visualizes continuous multi-period SVG trend curve.
- **Bar Mode** (`data-mode="bar"`): Visualizes engine-by-engine breakdown columns.

The tester verifies that:
1. Clicking the Bar button mutates `state.overviewChartMode` to `"bar"`, adds `.black` to the Bar button, and mounts `.ov-bars`.
2. Clicking the Line button mutates `state.overviewChartMode` to `"line"`, adds `.black` to the Line button, and mounts `svg.ov-chart`.
3. Transition occurs synchronously without visual artifacting or runtime errors.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Segmented Controls**: `.ov-mode-seg` container present.

---

## 4. Gherkin Scenario

```gherkin
Feature: Chart Visualization Mode Switching
  As a data analyst
  I want to switch seamlessly between longitudinal line curves and cross-engine bar columns
  So that I can analyze both overall visibility momentum and engine-specific market share.

  Scenario Outline: Switching visualization mode between line and bar
    Given the user is on the Overview Dashboard
    When the user clicks the mode button for "<TargetMode>"
    Then "state.overviewChartMode" should equal "<TargetMode>"
    And the button "[data-action='toggle-overview-mode'][data-mode='<TargetMode>']" should have class "black"
    And the element "<ExpectedContainer>" should be rendered in the DOM
    And the alternate container "<HiddenContainer>" should not be present

    Examples:
      | TargetMode | ExpectedContainer  | HiddenContainer |
      | bar        | .ov-bars           | svg.ov-chart    |
      | line       | svg.ov-chart       | .ov-bars        |
```

---

## 5. Visual Checks
- **Segmented Buttons**: Two buttons inside `.ov-mode-seg`.
- **Active Button**: Highlighted with dark theme background (`.btn.black`).
- **DOM Container**: `.ov-kpi-chart` swaps between hosting SVG canvas and `.ov-bars` flex columns.

---

## 6. Data and Network Checks
- **DOM & State Assertion**:
  ```javascript
  const modeSwitchCheck = await js(String.raw`(() => {
    // 1. Switch to Bar
    const barBtn = document.querySelector('[data-action="toggle-overview-mode"][data-mode="bar"]');
    if (barBtn) barBtn.click();
    const modeAfterBar = window.state?.overviewChartMode;
    const hasBars = !!document.querySelector('.ov-bars');

    // 2. Switch back to Line
    const lineBtn = document.querySelector('[data-action="toggle-overview-mode"][data-mode="line"]');
    if (lineBtn) lineBtn.click();
    const modeAfterLine = window.state?.overviewChartMode;
    const hasSvg = !!document.querySelector('svg.ov-chart');

    return {
      barSuccess: modeAfterBar === 'bar' && hasBars,
      lineSuccess: modeAfterLine === 'line' && hasSvg,
      noError: !window.__lastError
    };
  })()`);
  if (!modeSwitchCheck.barSuccess || !modeSwitchCheck.lineSuccess || !modeSwitchCheck.noError) {
    throw new Error('Chart mode switching assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-chart-mode-switching/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or test runner.
  - Screenshots of Line mode and Bar mode captured in result directory.
  - SCP sync from MacBook to host before final test report delivery.
