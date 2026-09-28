# TC-DB-02: Visualization Widget Catalog and Chart vs Table View Modes

## 1. Case ID and Purpose
- **Case ID:** `TC-DB-02`
- **Purpose:** Verify that each of the 16 analytical visualization types defined in `VIZ_BY_KEY` can be rendered, and that widgets supporting dual modes cleanly toggle between SVG interactive chart mode and tabular data grid mode without layout distortion.
- **Target Result Directory:** `02-dashboards-and-exports/02-gherkin-result-case-widget-creation-and-modes/`

---

## 2. Tester Brief
Each analytical visualization widget is registered with supported presentation modes (`modes: ["chart", "table"]` or `["table"]`).
1. In Chart mode, the widget renders SVG trend lines, stacked bars, or distribution rings.
2. Clicking the mode toggle button `[data-action="dash-viz-mode"]` switches to Table mode.
3. In Table mode, the card renders a formatted data table with column headers, formatted metric cells, and sorting arrows.
4. Independent filtering by topic, platform, or brand must immediately re-render the visualization in either mode.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/dashboards`.
- **Fixtures & Placeholders:**
  - `[DOMAIN]`: `zeo.org`
  - `[VIZ_TYPES]`: `vis-score`, `sov`, `platform-matrix`, `cit-share`

---

## 4. Gherkin Scenario

```gherkin
Feature: Visualization Widget Modes and Catalog

  Scenario Outline: Toggling between Chart and Table modes on analytical widgets
    Given a dashboard widget of type "<VizType>" is rendered on the dashboard
    And the initial presentation mode is "<InitialMode>"
    When the user clicks the mode toggle button "[data-action='dash-viz-mode']"
    Then the widget presentation should switch to "<TargetMode>"
    And the visual container should render "<ExpectedDOMSelector>"

    Examples:
      | VizType   | InitialMode | TargetMode | ExpectedDOMSelector |
      | vis-score | chart       | table      | .viz-table          |
      | vis-score | table       | chart      | svg.viz-chart       |
      | sov       | chart       | table      | .viz-table          |
```

---

## 5. Visual Checks
- **Chart Mode:**
  - SVG Container: `svg.viz-chart` or `.chart-container svg`.
  - Tooltips: Data point hover highlights.
- **Table Mode:**
  - Table Element: `table.viz-table` or `.table-wrap table`.
  - Column Headers: `th` containing metric labels.
- **Screenshot Points:**
  - `01_widget_chart_mode.png` (Widget displaying SVG line/bar chart).
  - `02_widget_table_mode.png` (Same widget toggled to data table view).

---

## 6. Data and Network Checks
- **Widget State:**
  - `viz.mode` updates between `"chart"` and `"table"`.
- **Data Integrity:**
  - Metrics in Table mode must match data points rendered in Chart mode.

---

## 7. Evidence and Reporting
- **Result Directory:** `02-dashboards-and-exports/02-gherkin-result-case-widget-creation-and-modes/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-dash-modes');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/dashboards', { wait: true, timeout: 30 });
await wait(2);

const modeToggleCheck = await js(String.raw`(() => {
  const card = document.querySelector('.viz-card');
  if (!card) return { found: false };

  const modeBtn = card.querySelector('[data-action="dash-viz-mode"]');
  const initialMode = card.getAttribute('data-mode') || 'chart';

  if (modeBtn) modeBtn.click();

  const newMode = card.getAttribute('data-mode');
  const hasTable = !!card.querySelector('.viz-table, table');
  const hasChart = !!card.querySelector('svg.viz-chart, svg');

  return {
    found: true,
    initialMode,
    newMode,
    hasTable,
    hasChart
  };
})()`);

cliLog('Mode Toggle Result: ' + JSON.stringify(modeToggleCheck));
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-dash-modes', { keep: false })`.
