# Case 05: Dual-Mode SVG Chart Visualization & Longitudinal Trend Curves

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-05`
- **Purpose**: Verify that drilling into a keyword prompt opens the Keyword Workspace with complete filter controls, and that the volume visualization canvas seamlessly toggles between SVG Bar Chart mode (`data-mode="bar"`) and SVG Line Chart mode (`data-mode="line"`), rendering proportional elements for all 4 AI platforms (ChatGPT, Perplexity, Gemini, Claude), labeling weekly time series intervals (`VOL_WEEK_LABELS`), and surfacing native interactive SVG tooltips.

## 2. Tester Brief
The tester selects a prompt row from the table or clicks the inspect button to launch the Keyword Workspace. The tester observes the default Bar Chart visualization, clicks the Line Chart toggle button, and verifies that the canvas redraws from vertical rectangular bars (`<rect>`) to continuous curved paths (`<path>`) with circular coordinate points (`<circle>`). The tester verifies that the horizontal axis switches to weekly interval labels, hovers over coordinate points to confirm `<title>` tooltip text, and switches back to Bar Chart mode.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Active Keyword: `[KEYWORD_TERM]` (e.g. "inverter klima")
  - Platforms: ChatGPT, Perplexity, Gemini, Claude
  - Chart Modes: `bar`, `line`
- **Prerequisites**:
  - Prompt Volumes page loaded.

## 4. Gherkin Scenario

```gherkin
Feature: Dual-Mode SVG Chart Canvas & Time Series Trends
  As an AI Search Analyst
  I want to switch between snapshot bar charts and historical trend line curves
  So that I can analyze weekly fluctuations in prompt generation across AI engines

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    And the user selects a prompt row to open the Keyword Workspace ".vol-chart-card"
    And the active keyword workspace header ".vol-kw-workspace-head" is displayed

  Scenario: Verify default Bar Chart rendering
    Then the Bar Chart mode button "button.vol-toggle-btn[data-mode='bar']" should have class ".active"
    And the SVG canvas "svg.vol-svg-chart" should render distinct SVG "<rect>" elements for each platform
    And the chart legend ".vol-chart-legend" should display platform color swatches and volume metrics

  Scenario: Switch to Line Chart mode and verify weekly time series paths
    When the user clicks the Line Chart toggle "button.vol-toggle-btn[data-mode='line']"
    Then the active chart mode "window.volumesState.chartConfig.mode" should be "line"
    And the Line Chart button should have active class ".active"
    And the SVG canvas "svg.vol-svg-chart" should render at least 4 SVG "<path>" elements
    And the horizontal axis labels should display weekly date intervals
    And hovering over any coordinate circle "<circle>" should display a native tooltip containing platform and volume

  Scenario: Switch back to Bar Chart mode cleanly
    Given the chart is currently in Line mode
    When the user clicks the Bar Chart toggle "button.vol-toggle-btn[data-mode='bar']"
    Then the SVG canvas should redraw with vertical rectangular bars
    And the active mode should be restored to "bar"
```

## 5. Visual Checks
- **Bar Mode**: 4 platform bars grouped side-by-side with brand theme colors.
- **Line Mode**: Smooth bezier curves with subtle stroke widths and hover-highlighted coordinate circles.
- **Legend Swatches**: Small circular color swatches aligned with platform names.

## 6. Data and Network Checks
- **DOM & State Assertions**:
  ```javascript
  const st = window.volumesState;
  assert.strictEqual(st.chartConfig.mode, 'line');
  const pathCount = document.querySelectorAll('svg.vol-svg-chart path').length;
  assert.ok(pathCount >= 4, 'Should render paths for 4 platforms');
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-dual-chart-visualization-and-trend-curves/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-05-chart-bar-mode.png`
     - `/tmp/ego-shots/tc-vol-05-chart-line-mode.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-05-*.png ./02-gherkin-result-case-dual-chart-visualization-and-trend-curves/
     ```
