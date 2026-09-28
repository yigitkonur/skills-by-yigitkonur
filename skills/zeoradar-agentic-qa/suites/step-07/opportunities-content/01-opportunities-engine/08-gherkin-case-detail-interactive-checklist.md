# Test Case: TC-OPP-08 - Opportunity Implementation Checklist & Progress Tracking

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-08`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenario `TC-OPP-10` (Interactive Checklist Toggling)
- **Purpose:** Verify that in the Opportunity Detail View, the Implementation Guide accordion renders a step-by-step actionable checklist (`.opp-checklist`), that clicking individual checklist items toggles their state between incomplete (dashed border box) and completed (solid green box with SVG checkmark and `.opp-done` class), applies strike-through text formatting, and dynamically increments the completion counter in the accordion header metadata.

---

## 2. Tester Brief
The tester will verify interactive checklist behavior within the detail view:
1. The "Implementation Guide" accordion section is expanded by default (or expands when clicked).
2. The accordion header metadata `.opp-accordion-meta` shows initial completion status (e.g. `0 / 3 completed`).
3. Each item `.opp-checklist-item` contains an interactive checkbox indicator `.opp-checkbox` and instructional text.
4. Clicking step 1 triggers `opp-toggle-step`:
   - Adds `.opp-done` class to the checklist item.
   - Converts the dashed border `.opp-checkbox` into a solid green checkmark.
   - Applies line-through style to the step text.
   - Increments the metadata counter to `1 / 3 completed`.
5. Clicking step 1 again unchecks it, reverting `.opp-done` and decrementing the counter back to `0 / 3 completed`.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Opportunity Under Test `[OPPORTUNITY_ID]`:** Active opportunity with defined implementation steps
- **Matching Result Directory:** `08-gherkin-result-case-detail-interactive-checklist/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Interactive Implementation Checklist Toggling and Completion Counter

  Background:
    Given the user has opened the detail view for opportunity "[OPPORTUNITY_ID]"
    And the Implementation Guide accordion ".opp-accordion[data-sec='implementation']" is expanded
    And the checklist contains 3 actionable steps

  Scenario Outline: Toggling Individual Checklist Steps
    When the user clicks checklist item "<StepIndex>"
    Then the checklist item "<StepIndex>" should have class "opp-done"
    And its checkbox element ".opp-checkbox" should render a green checkmark
    And the accordion header meta text should display "<ExpectedProgressMeta>"
    
    When the user clicks checklist item "<StepIndex>" a second time
    Then the checklist item "<StepIndex>" should not have class "opp-done"
    And its checkbox element should revert to a dashed border
    And the accordion header meta text should revert to "0 / 3"

    Examples:
      | StepIndex | ExpectedProgressMeta |
      | 1         | 1 / 3                |
      | 2         | 1 / 3                |
      | 3         | 1 / 3                |

  Scenario: Sequential Completion of All Checklist Steps
    When the user clicks checklist item 1
    And the user clicks checklist item 2
    And the user clicks checklist item 3
    Then all 3 checklist items should have class "opp-done"
    And the accordion header metadata ".opp-accordion-meta" should display "3 / 3" or "All completed"
```

---

## 5. Visual Checks
1. **Dashed Box (Unchecked):** `.opp-checkbox` renders with `2px dashed var(--border)` or `rgba(255,255,255,0.3)`.
2. **Solid Green Box (Checked):** `.opp-checklist-item.opp-done .opp-checkbox` renders with `background: var(--green)` and an inline white SVG checkmark.
3. **Strike-Through Text:** Step instructional text inside `.opp-checklist-item.opp-done` receives `text-decoration: line-through` and muted opacity (`opacity: 0.6`).
4. **Header Progress Badge:** `.opp-accordion-meta` displays progress count (e.g. `1 / 3` or `1 / 3 tamamlandı`).

---

## 6. Data and Network Checks
1. **Step State in Memory:**
   - Inspect `op.implementationSteps[stepIdx].done`.
   - Verify it toggles between `true` and `false`.
2. **Local Storage Persistence:**
   - Assert `localStorage.getItem("zeo-radar-opps-" + projKey)` reflects updated `implementationSteps` states upon toggling.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `08-gherkin-result-case-detail-interactive-checklist/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `checklist_initial_0_of_3.png` showing unchecked steps.
  2. Capture `checklist_step_1_done.png` showing checked step and updated header meta.
  3. Capture `checklist_all_done.png` showing all 3 steps completed.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-checklist/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/08-gherkin-result-case-detail-interactive-checklist/
     ```
  5. Include checklist assertions in `result.md`.

### Pass/Fail Criteria
- [ ] Checklist items toggle completion state on click without lag.
- [ ] Checked item visually displays solid green background, SVG checkmark, and struck-through text.
- [ ] Header progress counter increments and decrements dynamically.
- [ ] Checklist state persists when navigating away from and back to the opportunity.
