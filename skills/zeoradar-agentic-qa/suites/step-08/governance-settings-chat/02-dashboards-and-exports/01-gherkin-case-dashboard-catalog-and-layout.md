# TC-DB-01: Dashboard Template Catalog and Custom Layout Builder

## 1. Case ID and Purpose
- **Case ID:** `TC-DB-01`
- **Purpose:** Verify that a user can switch between curated dashboard templates (Executive, Citations, Sentiment, Platforms), add new visualization widgets via the builder modal, configure column spans, and rearrange the grid layout without visual defects.
- **Target Result Directory:** `02-dashboards-and-exports/01-gherkin-result-case-dashboard-catalog-and-layout/`

---

## 2. Tester Brief
Dashboards provide customized analytical arrangements for executives and analysts.
1. The user navigates to the Dashboards page (`#/[SLUG]/dashboards`).
2. The template picker allows selecting pre-built presets or creating a custom dashboard.
3. Clicking `[data-action="dash-add-viz"]` opens the visualization editor modal.
4. Selecting a visualization type (e.g. `sov` - Share of Voice) and confirming adds a new `.viz-card` to the dashboard grid.
5. **Execution Model:** Ego Browser operates on the remote MacBook. Screenshots are downloaded via SCP into the result directory.

---

## 3. Inputs and Prerequisites
- **Authenticated User:** `e2e-agent@zeogen.com`.
- **Target Route:** `[APP_URL]/#/[SLUG]/dashboards`.
- **Fixtures & Placeholders:**
  - `[DOMAIN]`: `zeo.org`
  - `[DASHBOARD_ID]`: `dash_custom_01`
  - `[VIZ_TYPE]`: `sov` (Share of Voice)

---

## 4. Gherkin Scenario

```gherkin
Feature: Dashboard Layout and Template Management

  Scenario Outline: Selecting dashboard template and adding a new visualization card
    Given the test user is on the Dashboards route "#/[SLUG]/dashboards"
    When the user selects the dashboard template "<TemplateName>"
    Then the dashboard surface should render the widget grid ".dash-grid"
    When the user clicks the "Add Visualization" button "[data-action='dash-add-viz']"
    Then the visualization modal ".viz-editor-modal" should be open
    When the user selects visualization type "<VizType>"
    And the user clicks the save widget button "[data-action='viz-save']"
    Then the modal should close
    And the dashboard grid should contain a widget card for "<VizType>"

    Examples:
      | TemplateName | VizType |
      | Executive    | sov     |
      | Sentiment    | sent-score |
```

---

## 5. Visual Checks
- **Surface Elements:**
  - Header: `.dash-top` with dashboard title and export actions.
  - Grid: `.dash-grid` containing `.viz-card` elements.
  - Add Widget Button: `button[data-action="dash-add-viz"]`.
- **Modal Elements:**
  - Container: `.viz-editor-modal` or `.modal-card`.
  - Type Selector: `[data-field="viz-type"]` or `select[name="viz-type"]`.
  - Save Button: `[data-action="viz-save"]`.
- **Screenshot Points:**
  - `01_dashboard_catalog_view.png` (Baseline dashboard grid).
  - `02_add_widget_modal_open.png` (Modal with visualization type selector).
  - `03_dashboard_with_new_widget.png` (Grid after adding new widget).

---

## 6. Data and Network Checks
- **State Assertion:**
  - `window.dashState().currentDashboard.vizzes.length` increments by 1.
  - Newly added viz object contains `{ type: "sov", mode: "chart" }`.

---

## 7. Evidence and Reporting
- **Result Directory:** `02-dashboards-and-exports/01-gherkin-result-case-dashboard-catalog-and-layout/`
- **Execution Script:**
```bash
ego-browser nodejs << 'EOF'
const task = await useOrCreateTaskSpace('e2e-dash-layout');
const tab = await openOrReuseTab('[APP_URL]/#/[SLUG]/dashboards', { wait: true, timeout: 30 });
await wait(2);

const initialCount = await js(String.raw`(() => document.querySelectorAll('.viz-card').length)()`);
cliLog('Initial widget count: ' + initialCount);

// Open Add Viz Modal
await click('[data-action="dash-add-viz"]');
await wait(1);

await js(String.raw`(() => {
  const sel = document.querySelector('[data-field="viz-type"]') || document.querySelector('select[name="viz-type"]');
  if (sel) { sel.value = 'sov'; sel.dispatchEvent(new Event('change', { bubbles: true })); }
})()`);

await click('[data-action="viz-save"]');
await wait(2);

const finalCount = await js(String.raw`(() => document.querySelectorAll('.viz-card').length)()`);
cliLog('Final widget count: ' + finalCount);
if (finalCount <= initialCount) {
  throw new Error('New widget failed to append to dashboard grid');
}
EOF
```
- **Teardown:** Call `completeTaskSpace('e2e-dash-layout', { keep: false })`.
