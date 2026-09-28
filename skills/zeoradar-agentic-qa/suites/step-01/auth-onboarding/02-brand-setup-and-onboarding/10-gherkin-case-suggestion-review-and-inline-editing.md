# Test Case: Suggestion Review Accordion, Inline Prompt Editing & Inclusion Gating

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-10-SUGGESTION-INLINE-EDIT`
- **Purpose:** Validate the Step 5 review screen (`activeStep === 5`), accordion grouping by topic, inline prompt query editing (`#ob-live-edit-first`, `.ob-action-check`), row inclusion toggling (`.ob-sel-toggle`, `.ob-row-off`), dynamic total accepted prompt count recalculation, and persona prompt binding suggestions.

---

## 2. Tester Brief
The tester advances to Step 5 (Review Prompts). The tester inspects the grouped prompt rows under their respective topic headers. The tester toggles an individual prompt's inclusion checkbox off, asserting that the row receives `.ob-row-off` and the total prompt badge counter decrements by 1. Next, the tester clicks the inline "Edit" button on a prompt row, alters the prompt query text in the auto-focused input `#ob-live-edit-first`, saves the change, and confirms that the updated text is rendered in the draft state. Finally, the tester tests canceling an inline edit.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** Step 5 (`activeStep === 5`), prompts generated and loaded into draft
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[ORIGINAL_PROMPT]`: Default generated prompt string
  - `[EDITED_PROMPT]`: Modified prompt string (`"[SAMPLE_PROMPT]"`, e.g. `"Daikin Altherma ısı pompası elektrik tüketimi"`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Step 5 - Prompt Review and Inline Editing

  Background:
    Given the user is on Step 5 of the onboarding wizard at "[APP_URL]/#/onboarding"
    And the total prompt badge ".ob-total-prompts-badge strong" displays the initial count

  @sanity @review @toggle
  Scenario: Toggling prompt inclusion updates row style and total badge count
    Given the initial prompt count is "N"
    When the user clicks the selection toggle "button.ob-sel-toggle" on the first prompt row
    Then the prompt row should acquire class "ob-row-off"
    And the total prompts count should decrement to "N - 1"
    When the user clicks the selection toggle again
    Then the class "ob-row-off" should be removed
    And the total prompts count should increment back to "N"

  @positive @inline-edit @save
  Scenario: Editing prompt query inline commits modified text to draft state
    When the user clicks the edit button "button.ob-row-edit-btn" on the first prompt row
    Then the row should switch to edit mode with class "ob-prompt-row-editing"
    And the input "input#ob-live-edit-first" should be visible and focused
    When the user types "[EDITED_PROMPT]" into "input#ob-live-edit-first"
    And clicks the save button ".ob-row-actions-edit .ob-action-check"
    Then the row should exit edit mode
    And the prompt text should display "[EDITED_PROMPT]"
    And "window.state.onboarding.live.draft.prompts[0].text" should equal "[EDITED_PROMPT]"

  @positive @inline-edit @cancel
  Scenario: Canceling inline edit reverts changes without saving
    When the user clicks "button.ob-row-edit-btn" on a prompt row
    And changes the input text to "Discarded Changes"
    And clicks the cancel button ".ob-row-actions-edit .ob-action-cancel" or presses Escape
    Then the row should exit edit mode
    And the prompt text should retain its original text "[ORIGINAL_PROMPT]"
```

---

## 5. Visual Checks
- **Accordion Table Container:**
  - Container `.ob-accordion-table-container` holds sections for Prompts, Personas, and Keywords.
  - Section headers `.ob-live-section-title` show count badges.
  - Topic group subheadings `.ob-live-topic-label` group relevant prompts cleanly.
- **Row States:**
  - Active: Standard dark text, checkbox checked with accent color.
  - Inactive (`.ob-row-off`): Strikethrough or muted grey text (opacity 0.5), checkbox unchecked.
  - Editing (`.ob-prompt-row-editing`): Input replaces plain text with save/cancel icons.

---

## 6. Data & Network Checks
- **Draft State Assertions (`assets/onboarding.js:3250`):**
  ```javascript
  const draft = window.state.onboarding.live.draft;
  assert(Array.isArray(draft.prompts), "Draft prompts array must exist");
  assert(draft.prompts.length > 0, "Must contain at least 1 prompt");
  ```
- **Total Count Invariant:**
  - `document.querySelector('.ob-total-prompts-badge strong').textContent === String(draft.prompts.filter(p => p.selected !== false).length)`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `10-gherkin-result-case-suggestion-review-and-inline-editing/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, edit transaction logs, count recalculation checks.
  - `evidence.json`: Snapshots of draft prompts array before and after edit.
  - `screenshots/01-review-accordion-initial.png`: Initial grouped prompts display.
  - `screenshots/02-prompt-row-toggled-off.png`: Prompt row with `.ob-row-off` style.
  - `screenshots/03-prompt-inline-editing.png`: Active inline edit input.
  - `screenshots/04-prompt-edited-saved.png`: Committed prompt with updated query string.
- **MacBook Execution Protocol:** Ego Browser interacts with accordion rows on MacBook; visual artifacts retrieved via SCP.
