# Test Case: Line Mode SVG Trend Chart Rendering

## 1. Case ID and Purpose
- **Case ID**: `TC-STEP03-TREND-01`
- **Purpose**: Verify that the Overview Dashboard renders the primary Visibility Trend Chart in SVG line mode (`ovLineSVG`), producing valid SVG elements, grid lines, Y-axis percentage labels, X-axis date interval ticks, accent gradient area fill, and sub-pixel coordinate alignment without layout jitter.

---

## 2. Tester Brief
In `line` chart mode (the default), the hero visibility card renders `svg.ov-chart[viewBox="0 0 600 160"]`.
Key rendering elements include:
- 3 dashed horizontal grid lines (`line.ov-grid-line`) with Y-axis percentage labels (`text.ov-ax`).
- X-axis date labels derived from `ovAxis(p)` anchored at start, middle, and end.
- Primary visibility trend path (`path[stroke="var(--accent)"]`) and subtle gradient area fill (`path[fill="var(--accent)"][fill-opacity=".07"]`).
- Invisible hit capture rect (`rect.ov-hit`) containing JSON payload `data-ov`.

The tester verifies that these SVG structures exist, contain valid numbers in their `d` attributes (no `NaN`), and adapt cleanly to container dimensions.

---

## 3. Inputs and Prerequisites
- **Target URL**: `[APP_URL]/#/[SLUG]/overview`
- **Mode Setting**: `state.overviewChartMode = "line"`

---

## 4. Gherkin Scenario

```gherkin
Feature: Line Mode SVG Visibility Trend Chart Rendering
  As an executive reviewing brand visibility trends
  I want to see a crisp, continuous SVG line chart with date intervals and percentage axes
  So that I can immediately track whether brand visibility is growing or declining over time.

  Scenario Outline: Rendering SVG line chart across different timeframes
    Given the user is on the Overview Dashboard in "line" chart mode
    When the user selects the timeframe "<Range>"
    Then the SVG element "svg.ov-chart" should be rendered inside ".ov-kpi-chart"
    And the SVG "viewBox" should equal "0 0 600 160"
    And the SVG should contain at least 3 horizontal grid lines "line.ov-grid-line"
    And the main trend path should have a valid "d" attribute without "NaN" or "undefined"
    And the hit detection rect "rect.ov-hit" should carry a valid "data-ov" JSON payload

    Examples:
      | Range | ExpectedTicksMin |
      | 7d    | 4                |
      | 14d   | 4                |
      | 30d   | 4                |
      | 90d   | 4                |
```

---

## 5. Visual Checks
- **Chart Container**: `.ov-kpi-chart` hosting `div.ov-chart-wrap.ov-plain`.
- **SVG Elements**: `svg.ov-chart` with viewBox `0 0 600 160`.
- **Trend Path**: Purple accent path (`--accent`) with semi-transparent area fill underneath.
- **Axis Ticks**: Neat numeric axis text (`text.ov-ax`) aligned at the left and bottom edges.

---

## 6. Data and Network Checks
- **DOM & Path Verification**:
  ```javascript
  const svgCheck = await js(String.raw`(() => {
    const svg = document.querySelector('.ov-kpi-chart svg.ov-chart');
    if (!svg) return { error: 'SVG not found' };

    const path = svg.querySelector('path[stroke="var(--accent)"]');
    const d = path?.getAttribute('d') || '';
    const hasNan = d.includes('NaN') || d.includes('undefined');
    const hit = svg.querySelector('rect.ov-hit');
    const rawData = hit?.getAttribute('data-ov');
    let parsedOk = false;
    try {
      const parsed = JSON.parse(rawData);
      parsedOk = Array.isArray(parsed.xs) && Array.isArray(parsed.series);
    } catch (e) {}

    return {
      hasSvg: true,
      hasNan,
      pathValid: d.startsWith('M') && d.length > 10,
      parsedOk,
      noError: !window.__lastError
    };
  })()`);
  if (!svgCheck.hasSvg || svgCheck.hasNan || !svgCheck.pathValid || !svgCheck.parsedOk) {
    throw new Error('SVG Line mode rendering assertion failed');
  }
  ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-line-mode-svg-rendering/`
- **Execution Model**:
  - Run via `ego-browser nodejs` on MacBook or Linux VM.
  - Screenshots of SVG chart rendered across 7D and 30D saved in result directory.
  - SCP sync from MacBook to host before logging final test report.
