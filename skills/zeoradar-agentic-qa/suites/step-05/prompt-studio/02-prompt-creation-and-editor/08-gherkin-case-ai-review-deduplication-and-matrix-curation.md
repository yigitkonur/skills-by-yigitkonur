# Test Case 08: Discovered Prompt Review Matrix, Inline Editing & Duplicate Default Deselect

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-08-REVIEW-DEDUPLICATION`
- **Purpose**: Verify that Step 3 (Review & Curation Matrix) of the AI Discovery Wizard correctly evaluates deduplication keys against existing database prompts, flags matching items with `.dg-dup-row` and `"Duplicate (Existing)"` badges, deselects them by default (`selected: false`), and provides responsive inline text editing, brand/non-brand type toggles, and item deletion controls prior to PostgreSQL commit.

---

## 2. Tester Brief
The tester will:
1. Complete AI Discovery generation or load mock candidate prompts into Step 3 containing at least one query that matches an existing active project prompt.
2. In the Review step, verify that:
   - Summary strip displays `"X of Y selected"`.
   - Alert badge renders `"N existing duplicates detected"`.
   - The duplicate candidate row carries class `tr.dg-dup-row`, displays a red badge `"Duplicate (Existing)"`, and its checkbox is unchecked by default.
   - Genuine new candidates display a green badge `"New"` and are checked by default.
3. Use the Select All and Deselect All buttons and confirm all checkboxes toggle accordingly.
4. Filter by topic using `.wizard-topic-item` in the left sidebar.
5. In an active candidate row:
   - Edit the query text inline via `input[data-action-input="dg-discover-edit-text"]`.
   - Click the type toggle button `button[data-action="dg-discover-toggle-type"]` to switch between `"Brand"` and `"Non-brand"`.
   - Click the remove button `button[data-action="dg-discover-remove-item"]` and confirm the row is removed from the curation batch.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Pre-existing Prompts**: At least 1 existing prompt (e.g. `"[BRAND] inverter klimalar"`) present in the project database.
- **Component Selectors**:
  - Review Table: `table.tbl.csv-rev-tbl`
  - Duplicate Row: `tr.dg-dup-row`
  - Inline Text Input: `input.wizard-input[data-action-input="dg-discover-edit-text"]`
  - Type Toggle: `button[data-action="dg-discover-toggle-type"]`
  - Remove Candidate: `button.danger[data-action="dg-discover-remove-item"]`
  - Select All / Deselect All: `button[data-action="dg-discover-select-all"]`, `button[data-action="dg-discover-deselect-all"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: AI Discovery Review Matrix Curation & Duplicate Pre-Deselection

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And the AI Discovery Wizard is mounted on Step 3 "review" with synthesized candidates
    And candidate item matches an existing project prompt

  @smoke @ai-wizard @deduplication
  Scenario: Duplicate candidates are highlighted and deselected by default
    When the tester inspects the review matrix "table.tbl.csv-rev-tbl"
    Then the candidate matching the existing prompt should carry class "tr.dg-dup-row"
    And its checkbox "input[data-action='dg-discover-toggle-item']" should be unchecked
    And its duplicate status badge should display "Duplicate (Existing)"
    And novel candidate items should display the status badge "New" with checked checkboxes
    And the summary alert should display "1 existing duplicates detected"

  @curation @inline-edit
  Scenario: Tester modifies candidate query text and toggles brand classification inline
    When the tester edits candidate text input "input[data-action-input='dg-discover-edit-text']" to "Daikin Altherma Isı Pompası Fiyatları"
    Then the in-memory item text should update immediately
    When the tester clicks the type toggle button "button[data-action='dg-discover-toggle-type']"
    Then the button label should toggle from "Brand" to "Non-brand"
    And the in-memory item type should update to "non_brand"

  @curation @removal
  Scenario: Remove candidate item from discovery batch
    Given 10 candidate prompts are rendered in the review matrix
    When the tester clicks the delete action "button[data-action='dg-discover-remove-item']" on row 1
    Then row 1 should be removed from the table
    And the total candidate count should update to 9
```

---

## 5. Visual Checks
1. **Duplicate Row Contrast**: `tr.dg-dup-row` has a light red tint background (`#fee2e2` / light pink) clearly contrasting with standard rows.
2. **Badges Distinction**: `"Duplicate (Existing)"` renders in bold dark red text; `"New"` renders in emerald green.
3. **Sidebar Topic List**: Left sidebar `.wizard-topics-col` shows all generated topic clusters with count pills.

---

## 6. Data and Network Checks
1. **Deduplication Logic Check**:
   ```javascript
   const items = window.ZEO_PROMPT_DESIGNER._getState().items;
   const dupItem = items.find(it => it.isExistingDuplicate);
   if (dupItem) {
     assert.strictEqual(dupItem.selected, false, 'Duplicate item must be unselected by default');
     assert.strictEqual(dupItem.isExistingDuplicate, true, 'isExistingDuplicate flag must be set');
   }
   ```
2. **Batch Item Removal**: Verify array length in `designerState.items` decreases by 1 on delete.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-ai-review-deduplication-and-matrix-curation/`
- **Execution Model Notice**: Ego Browser drives automation on macOS. Matrix captures showing duplicate highlighting and inline edits are saved to `/tmp/shots/discovery-review-[STEP].png` and transferred via SCP.
- **Report Contents**:
  - `status.json`: Test execution log and assertion state.
  - `screenshot-review-duplicate-highlight.png`: Curation table showing `.dg-dup-row` and deselected checkbox.
  - `screenshot-review-inline-edited.png`: Row displaying edited query text and updated type badge.
