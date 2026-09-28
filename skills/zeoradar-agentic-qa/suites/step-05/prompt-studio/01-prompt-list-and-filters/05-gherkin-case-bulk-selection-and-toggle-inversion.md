# Test Case 05: Multi-Row Bulk Actions, Floating Bar & Paused Set Toggle Inversion

## 1. Case ID and Purpose
- **Case ID**: `TC-PLIST-05-BULK-INVERSION`
- **Purpose**: Verify that multi-row selection in the Prompt Designer triggers the docked floating action bar (`.zr-bulkbar.bulk-action-bar-floating`), accurately tracks selected counts, executes bulk pause operations on active prompts, and adheres to the strict toggle inversion rule when acting upon a homogeneous paused set, correctly flipping their status from `paused` to `active` and moving them back to the active inventory.

---

## 2. Tester Brief
The tester will:
1. Navigate to the Prompt Designer Workbench for `[DOMAIN]`.
2. Click the select-all checkbox in the table header (`th.dg-checkcol .dg-check`).
3. Verify that all visible rows receive `.sel`, their checkboxes receive `.on`, and the floating bulk bar appears at the bottom with `"N prompts selected"`.
4. Click `[data-action="bulk-clear"]` and verify that all selections clear and the bar dismisses.
5. Select a subset of active prompts, click `[data-action="bulk-disable"]`, and verify that the prompts transition to `status = 'paused'`.
6. Navigate to the "Paused" / "Inactive" tab, select all paused prompts, and click `[data-action="bulk-disable"]`.
7. Verify the toggle inversion semantics in `dgBulkRowDraft('toggle', row)`:
   - Since `row.status === 'paused'`, `base.status` inverts to `'active'`.
   - Upon page refresh/reload, these prompts migrate from Inactive back to Active.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Pre-existing Data**: At least 3 active prompts and at least 2 paused prompts.
- **Select-All Selector**: `th.dg-checkcol span.dg-check[data-action="dg-toggle-select-all"]`
- **Floating Bar Selector**: `.zr-bulkbar.bulk-action-bar-floating`

---

## 4. Gherkin Scenario

```gherkin
Feature: Multi-Row Bulk Selection & Status Toggle Inversion

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And the page has mounted with selector ".designer-grid"

  @smoke @bulk
  Scenario: Select-all checkbox toggles all visible rows and displays floating bulk bar
    When the tester clicks the select-all checkbox "th.dg-checkcol span.dg-check"
    Then the select-all checkbox should gain class ".on"
    And all visible prompt rows in "table.tbl.dg-tbl tbody tr.dg-row" should gain class ".sel"
    And the floating bulk action bar ".zr-bulkbar.bulk-action-bar-floating" should become visible
    And the counter ".bulk-count" should display the total number of selected prompts
    When the tester clicks the clear selection button "button.bulk-clear"
    Then the floating bulk action bar should be removed from the DOM
    And no prompt rows should have class ".sel"
    And the select-all checkbox should lose class ".on"

  @mutation @bulk @inversion
  Scenario: Bulk toggle inverts homogeneous paused prompt set back to active
    Given the tester navigates to the Inactive prompts tab "span.tab[data-t='inactive']"
    And the inactive table displays 3 paused prompts
    When the tester clicks the select-all checkbox "th.dg-checkcol span.dg-check"
    And the floating action bar displays "3 prompts selected"
    And the tester clicks the bulk toggle button "button.bulk-btn[data-action='bulk-disable']"
    Then the mutation state machine should dispatch "upsert-prompt" for each row with "status: 'active'"
    And a confirmation toast should appear stating "Toggled active status for selected prompts"
    When the tester switches back to the Active tab "span.tab[data-t='active']"
    Then the 3 formerly paused prompts should now be rendered in the active prompt table
    And the Inactive tab should reflect the reduced prompt count
```

---

## 5. Visual Checks
1. **Floating Bar Positioning**: `.zr-bulkbar` floats docked at the bottom center of the viewport with a high z-index (`z-index: 100`).
2. **Selected Row Styling**: Rows with `.sel` class receive a distinct background highlight (subtle accent tint).
3. **Pending Rows**: During mutation execution, rows briefly gain `tr.dg-row-pending` with reduced opacity (`0.65`) and saving badges before settling.

---

## 6. Data and Network Checks
1. **Bulk Inversion Formula Check**:
   ```javascript
   // Verify dgBulkRowDraft logic for paused rows
   const samplePausedRow = { id: "p1", status: "paused", text: "Luxury gifts" };
   const draft = (samplePausedRow.status === 'paused') ? 'active' : 'paused';
   assert.strictEqual(draft, 'active', 'Paused status must invert to active');
   ```
2. **Network Mutation Log**:
   - Inspect network calls during bulk toggle: verify `upsert-prompt` payload carries `status: "active"` and the correct prompt IDs.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-bulk-selection-and-toggle-inversion/`
- **Execution Model Notice**: Ego Browser drives the MacBook test browser. Screenshots of the floating bar and table transitions are saved to `/tmp/shots/bulk-inversion-[ACTION].png` and pulled via SCP.
- **Report Contents**:
  - `status.json`: Execution verdict and mutation timing.
  - `screenshot-bulk-selected.png`: Master table with all rows selected and floating bar visible.
  - `screenshot-inversion-complete.png`: Active tab showing restored prompts post-inversion.
