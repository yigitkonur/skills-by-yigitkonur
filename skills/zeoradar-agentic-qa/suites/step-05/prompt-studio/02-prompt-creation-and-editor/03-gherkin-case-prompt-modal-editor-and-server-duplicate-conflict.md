# Test Case 03: Inline & Modal Prompt Editor, Attribute Modification & Server Duplicate 409

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-03-EDITOR-DUPLICATE`
- **Purpose**: Verify that clicking the edit action on a prompt row launches the prefilled modal editor (`edit-prompt`), allows mutation of prompt text, topic assignment, brand type, and geographic scope, and gracefully manages server-side duplicate conflicts (`duplicate_prompt`), displaying actionable failure banners with retry and dismiss options.

---

## 2. Tester Brief
The tester will:
1. Open the Prompt Designer Workbench for `[DOMAIN]`.
2. Locate a specific prompt row and click its edit button `button[data-action="dg-edit-prompt"]`.
3. Verify that the modal opens with title `"Edit Prompt"` and all fields are prefilled with the prompt's existing attributes.
4. Modify the query text to append a specific modifier (e.g. `[PROMPT_TEXT]` + `" 2026 Edition"`).
5. Submit the modal via `button[data-action="apply-bulk-modal"][data-type="edit-prompt"]`.
6. Verify that the table updates with the modified text and the header displays `.dg-save-chip.saved`.
7. Re-open the edit modal, set the prompt text identical to another existing prompt in the project, and submit.
8. Verify that the server returns `duplicate_prompt`:
   - Header renders `.dg-save-chip.failed`.
   - Error message states `"A prompt with this text already exists."` (Turkish: `"Bu metne sahip bir prompt zaten var."`).
   - Retry (`dg-retry-save`) and dismiss (`dg-dismiss-save`) buttons are functional.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Pre-existing Prompts**: At least two distinct prompts (Prompt A and Prompt B) in the database.
- **Form Selectors**:
  - Edit Row Trigger: `button[data-action="dg-edit-prompt"][data-pid="[PROMPT_ID]"]`
  - Modal Form: `input#dgPromptText`, `select#dgPromptTopic`, `select#dgPromptType`
  - Error Chip: `span.dg-save-chip.failed`
  - Retry Action: `button[data-action="dg-retry-save"]`
  - Dismiss Action: `button[data-action="dg-dismiss-save"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: Prompt Modal Editing & Server Duplicate Conflict Handling

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And two active prompts "Prompt Alpha" and "Prompt Beta" exist in the project

  @smoke @editor @mutation
  Scenario: Successfully modify prompt text and attributes via modal editor
    When the tester clicks the edit button "button[data-action='dg-edit-prompt']" for "Prompt Alpha"
    Then the modal overlay ".overlay.dg-modal-root" should appear
    And the title should display "Edit Prompt"
    And the text input "#dgPromptText" should contain "Prompt Alpha"
    When the tester updates the text field to "Prompt Alpha - Revised Edition"
    And changes the prompt type to "brand"
    And clicks the save button "button[data-action='apply-bulk-modal'][data-type='edit-prompt']"
    Then the modal should close
    And the table row should display the updated text "Prompt Alpha - Revised Edition"
    And the header should display the save chip ".dg-save-chip.saved"

  @conflict @duplicate @error
  Scenario: Server duplicate prompt rejection triggers actionable error banner
    Given the tester opens the edit modal for "Prompt Alpha - Revised Edition"
    When the tester changes the prompt text to match "Prompt Beta" exactly
    And clicks the save button "button[data-action='apply-bulk-modal'][data-type='edit-prompt']"
    Then the server should return the error code "duplicate_prompt"
    And the workbench header should render the error chip ".dg-save-chip.failed"
    And the error banner should display "A prompt with this text already exists."
    And the retry button "button[data-action='dg-retry-save']" should be visible
    When the tester clicks the dismiss button "button[data-action='dg-dismiss-save']"
    Then the error chip should be dismissed from the workbench header
```

---

## 5. Visual Checks
1. **Edit Modal Prefill**: All inputs (`#dgPromptText`, `#dgPromptTopic`, `#dgPromptCountry`, `#dgPromptLocale`) immediately reflect current row values upon opening.
2. **Error Chip Styling**: `.dg-save-chip.failed` renders with light red background (`#fee2e2`), dark red text (`#991b1b`), and alert icon.
3. **Modified Dot**: If uncommitted edits exist in static mode, the modified 6px pink indicator `.dg-dot-mod` is visible next to the prompt text.

---

## 6. Data and Network Checks
1. **Server Conflict Error Contract**:
   ```javascript
   // Verify error chip structure upon duplicate mutation
   const failedChip = document.querySelector('.dg-save-chip.failed');
   assert.ok(failedChip !== null, 'Failed save chip must be rendered on duplicate conflict');
   assert.ok(
     failedChip.textContent.includes('duplicate_prompt') || failedChip.textContent.includes('zaten var'),
     'Error text must identify duplicate prompt conflict'
   );
   ```
2. **Retry Mutation ID Preservation**:
   - Verify that clicking `dg-retry-save` dispatches `upsert-prompt` reusing the same `clientMutationId`.

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-prompt-modal-editor-and-server-duplicate-conflict/`
- **Execution Model Notice**: Remote test automation runs via Ego Browser on macOS. Modal and error state screenshots are captured to `/tmp/shots/editor-duplicate-[STEP].png` and pulled via SCP.
- **Report Contents**:
  - `status.json`: Test execution log and mutation latency.
  - `screenshot-edit-modal-prefilled.png`: Prefilled modal on row edit.
  - `screenshot-edit-success.png`: Updated row with `.dg-save-chip.saved`.
  - `screenshot-duplicate-conflict-banner.png`: Red error banner with retry/dismiss actions.
