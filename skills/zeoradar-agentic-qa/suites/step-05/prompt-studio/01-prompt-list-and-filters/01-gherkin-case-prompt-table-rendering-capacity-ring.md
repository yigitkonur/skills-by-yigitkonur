# Test Case 01: Master Table Rendering, SVG Capacity Formula & 100-Prompt Cap

## 1. Case ID and Purpose
- **Case ID**: `TC-PLIST-01-CAPACITY-RING`
- **Purpose**: Verify that the master prompt table renders all active project prompts with correct taxonomy, column headers, engine badges, and that the SVG capacity ring accurately computes the stroke dash saturation according to the authoritative formula `dash = 40.2 * min(totalN, 100) / 100`, handling exact 100-item saturation, over-quota boundary conditions, and prompt archival decrements.

---

## 2. Tester Brief
The tester will navigate to the Prompt Designer Workbench for project `[DOMAIN]`. The tester must verify that:
1. The table header contains checkboxes, topic badges, prompt type chips, locale, and measurement engines.
2. The capacity counter `.count-pill` displays `<b>[CAPACITY_COUNT]</b> / 100 prompts`.
3. The SVG capacity ring circle `svg.ring circle:nth-child(2)` dynamically computes `stroke-dasharray="[STROKE_DASHARRAY] 40.2"`.
4. When saturated at 100 prompts, the ring is 100% full (`"40.2 40.2"`). Attempting to add an over-quota prompt triggers the plan limit guardrail.
5. Archiving/deleting an active prompt decrements the total count and contracts the SVG stroke dash proportionally.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Pre-existing Data**: Project loaded with active prompts across multiple topic clusters.
- **Test Accounts**: Authenticated user with project read/write privileges.
- **Dynamic Variables**:
  - `[CAPACITY_COUNT]`: Integer count of active prompts.
  - `[STROKE_DASHARRAY]`: Computed string representing `(40.2 * Math.min(count, 100) / 100)`.

---

## 4. Gherkin Scenario

```gherkin
Feature: Prompt Designer Workbench Master Table & Quota Saturation

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And the page has mounted with selector ".designer-grid"

  @smoke @ui @quota
  Scenario Outline: Verify SVG capacity ring stroke-dash calculation across prompt volumes
    Given the project has "<InitialCount>" active prompts configured
    When the tester inspects the capacity pill ".count-pill"
    Then the pill readout should display "<InitialCount>" with suffix "/ 100 prompts"
    And the SVG ring circle "svg.ring circle:nth-child(2)" should have stroke-dasharray "<ExpectedStroke>"
    And the prompt table "table.tbl.dg-tbl" should render "<RenderedRows>" visible rows

    Examples:
      | InitialCount | ExpectedStroke | RenderedRows |
      | 48           | 19.296 40.2    | 48           |
      | 75           | 30.15 40.2     | 75           |
      | 100          | 40.2 40.2      | 100          |

  @boundary @quota
  Scenario: Capacity ring boundary saturation and quota rejection at 100 items
    Given the project is saturated at exactly 100 active prompts
    When the tester inspects "svg.ring circle:nth-child(2)"
    Then the stroke-dasharray attribute must equal "40.2 40.2"
    When the tester clicks "button[data-action='dg-open-add-prompt']"
    And fills in the prompt query "[PROMPT_TEXT]" and submits the form
    Then the server should reject the creation with a quota limitation error
    And the total count in ".count-pill b" must remain "100"

  @mutation @quota
  Scenario: Quota decrement and ring contraction upon prompt archival
    Given the project currently has "100" active prompts
    When the tester selects an active prompt row in "table.tbl.dg-tbl"
    And clicks the bulk delete action ".bulk-btn[data-action='bulk-delete']"
    Then the command "archive-prompt" should be dispatched to the server
    And upon reload the capacity count in ".count-pill b" should decrement to "99"
    And the stroke-dasharray in "svg.ring circle:nth-child(2)" should contract to "39.798 40.2"
```

---

## 5. Visual Checks
1. **Workbench Top Bar**: `.designer-head h1` renders `"Prompt Designer"`. Subtitle `.designer-head .sub` is visible with descriptive copy.
2. **Capacity Counter Pill**: `.count-pill` has an inline circular SVG (`svg.ring`, 16x16 px) with background ring `stroke:var(--pink-200)` and foreground fill `stroke:var(--accent)`.
3. **Table Structure**: `table.tbl.dg-tbl` renders column headers: Checkbox, Prompts, Topic, Prompt Type, Language, Regions, Measurement Engines, Actions.
4. **Inline Add Row**: `tr.dg-addrow` is styled with dashed border and prompt placeholder `"+ Add a new prompt..."`.
5. **No Layout Shifts**: Capacity pill does not wrap or truncate on desktop viewports (1280px+).

---

## 6. Data and Network Checks
1. **Capacity Formula Execution**:
   ```javascript
   const circle = document.querySelector('svg.ring circle:nth-child(2)');
   const totalN = parseInt(document.querySelector('.count-pill b').textContent.trim(), 10);
   const strokeDash = circle.getAttribute('stroke-dasharray') || circle.style.strokeDasharray;
   const computedDash = (40.2 * Math.min(totalN, 100) / 100).toFixed(3);
   const actualDash = parseFloat(strokeDash.split(' ')[0]).toFixed(3);
   assert.strictEqual(actualDash, computedDash, 'Stroke dash must match 40.2 * min(totalN, 100) / 100');
   ```
2. **Server Command Payload**: On deletion, verify POST call to `archive-prompt` containing `{ projectId: "[PROJECT_ID]", promptId: "[PROMPT_ID]" }`.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-prompt-table-rendering-capacity-ring/`
- **Execution Model Notice**: Ego Browser executes remotely on a macOS host. Test runners must capture viewport screenshots into `/tmp/shots/capacity-ring-[STATE].png`, pull them via `scp macbook:/tmp/shots/capacity-ring-*.png <ResultDir>/`, and link them in the final evaluation report.
- **Report Contents**:
  - `status.json`: Execution verdict (`PASSED`/`FAILED`), runtime duration, prompt count.
  - `screenshot-table-initial.png`: Initial workbench render with capacity ring.
  - `screenshot-table-saturated.png`: 100-item saturated state.
  - `screenshot-table-decremented.png`: Post-archive 99-item state.
