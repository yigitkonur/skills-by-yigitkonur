# Case 10: Demographics Multi-Card View & Regional Heatmap Controls

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-10`
- **Purpose**: Verify that the Demographics suite renders 4 distinct demographic analysis cards (Gender Distribution Donut SVG, Age Cohorts Bar SVG, Annual Income Cohorts Bar SVG, and Regional World Choropleth Heatmap), that individual cards allow toggling between visual SVG chart mode and tabular data mode, and that the interactive choropleth heatmap responds smoothly to Zoom In, Zoom Out, and Zoom Reset controls.

## 2. Tester Brief
The tester switches to the Demographics tab (`data-tab="demographics"`), verifies that all 4 cards render their respective SVG graphics, toggles the Gender card into tabular data mode to inspect exact percentage breakdowns, and tests the heatmap zoom controls on the Regional card (asserting that clicking Zoom In increases scale above 1.0, Zoom Out decreases scale, and Zoom Reset restores exactly 1.0).

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Active Keyword: `[KEYWORD_TERM]` (e.g. "klima")
  - Cards: `gender`, `age`, `income`, `regional`
- **Prerequisites**:
  - Demographics tab active.

## 4. Gherkin Scenario

```gherkin
Feature: Demographics Visualizations & Regional Heatmap Interaction
  As an Audience Profiling Analyst
  I want to analyze consumer search volume across gender, age cohorts, income brackets, and regions
  So that I can tailor content and ad campaigns to primary demographic segments

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    And the user switches to the Demographics tab "button.volumes-tab-btn[data-tab='demographics']"
    And the demographics section header ".vol-sec-header" is displayed

  Scenario: Verify 4 core demographic cards render visual SVG charts
    Then the Gender card ".demographics-card-gender" should render an SVG donut chart ".vol-svg-gender"
    And the Age card ".demographics-card-age" should render age cohort bars
    And the Income card ".demographics-card-income" should render income bracket bars
    And the Regional card ".demographics-card-regional" should render the SVG world choropleth map

  Scenario: Toggle card view mode between visual chart and tabular breakdown
    When the user clicks the view toggle "button[data-action='vol-card-view-mode'][data-card='gender']"
    Then the Gender card should switch from SVG chart into a tabular breakdown table
    And the table should display percentage values for Female, Male, and Unspecified
    When the user clicks the view toggle again
    Then the Gender card should restore the SVG donut chart

  Scenario: Exercise Regional Heatmap interactive zoom controls
    When the user clicks the Zoom In button "button[data-action='vol-zoom-in']"
    Then the heatmap scale "window.volumesState.heatmapZoom" should increase above 1.0
    When the user clicks the Zoom Out button "button[data-action='vol-zoom-out']"
    Then the heatmap scale should decrease
    When the user clicks the Zoom Reset button "button[data-action='vol-zoom-reset']"
    Then the heatmap scale should reset to exactly 1.0
```

## 5. Visual Checks
- **Donut Chart**: 3 distinct segments with clean stroke separations.
- **Cohort Bars**: Horizontal/vertical bars with clean percentage labels.
- **Choropleth Heatmap**: 4-tier color ramp shading countries according to relative search interest.
- **Zoom Toolbar**: Floating or corner-mounted pill containing `+`, `-`, and reset icons.

## 6. Data and Network Checks
- **Zoom State Properties**:
  ```javascript
  const st = window.volumesState;
  assert.strictEqual(st.activeTab, 'demographics');
  assert.strictEqual(st.heatmapZoom, 1.0);
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-demographics-cohorts-and-heatmap/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-10-demographics-cards.png`
     - `/tmp/ego-shots/tc-vol-10-heatmap-zoomed.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-10-*.png ./02-gherkin-result-case-demographics-cohorts-and-heatmap/
     ```
