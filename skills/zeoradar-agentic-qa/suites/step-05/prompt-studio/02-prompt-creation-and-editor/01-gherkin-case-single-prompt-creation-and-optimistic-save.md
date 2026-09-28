# Test Case 01: Single Prompt Modal Creation, Optimistic Row & Server Save Settle

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-01-SINGLE-ADD-OPTIMISTIC`
- **Purpose**: Verify that creating a single prompt via the modal dialog captures all required attributes (text, topic, type, status, country, locale, intent), immediately renders an optimistic pending row (`tr.dg-row-pending`) with a `"Saving…"` indicator in the table, and successfully settles into active state upon server acknowledgement of the `upsert-prompt` command.

---

## 2. Tester Brief
The tester will:
1. Navigate to the Prompt Designer Workbench for `[DOMAIN]`.
2. Click the primary button `button[data-action="dg-open-add-prompt"]`.
3. Fill in the modal fields:
   - Query text: `[PROMPT_TEXT]`
   - Topic: `[TOPIC_NAME]`
   - Prompt Type: `non_brand`
   - Status: `active`
   - Country: `[COUNTRY]`
   - Locale: `[LANGUAGE]`
   - Intent: `[INTENT_TYPE]`
4. Submit the form via `button[data-action="apply-bulk-modal"][data-type="add-prompt"]`.
5. Verify that:
   - The modal closes immediately.
   - A pending row (`tr.dg-row-pending`) appears at the top of the table displaying opacity `0.65` and `"Saving…"`.
   - The workbench header displays the saving chip `.dg-save-chip.saving`.
   - Once the server responds with `{ ok: true }`, the row removes `.dg-row-pending`, the header updates to `.dg-save-chip.saved`, and the prompt is permanently added.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Form Selectors**:
  - Open Button: `button.btn.black.small[data-action="dg-open-add-prompt"]`
  - Text Input: `input#dgPromptText.wizard-input`
  - Topic Select: `select#dgPromptTopic.wizard-select`
  - Type Select: `select#dgPromptType.wizard-select`
  - Submit Button: `button[data-action="apply-bulk-modal"][data-type="add-prompt"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: Single Prompt Modal Creation & Optimistic Projection

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And the page has mounted with selector ".designer-grid"

  @smoke @modal @mutation
  Scenario Outline: Successfully create new prompt and observe optimistic row settlement
    When the tester clicks "button[data-action='dg-open-add-prompt']"
    Then the modal overlay ".overlay.dg-modal-root" should appear
    And the modal title should display "Add New Prompt"
    When the tester fills the modal form with:
      | Field    | Value            |
      | Text     | <PromptText>     |
      | Topic    | <TopicName>      |
      | Type     | <PromptType>     |
      | Status   | active           |
      | Country  | <Country>        |
      | Locale   | <Locale>         |
      | Intent   | <Intent>         |
    And clicks the submit button "button[data-action='apply-bulk-modal'][data-type='add-prompt']"
    Then the modal overlay should close
    And the master table should immediately prepend an optimistic row "tr.dg-row-pending"
    And the header should display the saving chip ".dg-save-chip.saving"
    When the server confirms the "upsert-prompt" mutation
    Then the pending row should remove class ".dg-row-pending"
    And the header chip should transition to ".dg-save-chip.saved"
    And the new prompt "<PromptText>" should be permanently visible in the table

    Examples:
      | PromptText                                      | TopicName             | PromptType | Country | Locale | Intent |
      | What are the most energy efficient heat pumps for homes? | Heating Solutions     | non_brand  | US      | en     | comm   |
      | Ev için en tasarruflu ısı pompası hangisi       | Isı Pompaları         | non_brand  | TR      | tr     | trans  |
```

---

## 5. Visual Checks
1. **Modal Presentation**: `.zr-wizard.wizard-frame.wizard-sm` is centered with clean inputs and labels.
2. **Pending Row Visual**: While saving, `tr.dg-row-pending` has opacity `0.65` and offline badge `.badge.dg-badge-off` with text `"Saving…"`.
3. **Save Chip**: Top navigation bar renders `.dg-save-chip.saved` with green check icon and text `"Saved"`.

---

## 6. Data and Network Checks
1. **Network Mutation Payload**:
   - Inspect POST request for `upsert-prompt`.
   - Verify payload matches:
     ```json
     {
       "projectId": "[PROJECT_ID]",
       "text": "[PROMPT_TEXT]",
       "topicId": "[TOPIC_ID]",
       "type": "non_brand",
       "status": "active",
       "country": "[COUNTRY]",
       "locale": "[LANGUAGE]",
       "intent": "[INTENT_TYPE]"
     }
     ```
2. **Optimistic Row DOM Check**:
   ```javascript
   const pendingRow = document.querySelector('tr.dg-row-pending');
   if (pendingRow) {
     assert.ok(pendingRow.textContent.includes('Saving'), 'Pending row must show saving status');
   }
   ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-single-prompt-creation-and-optimistic-save/`
- **Execution Model Notice**: Ego Browser drives automation on macOS. Viewport captures of the open modal, optimistic row, and settled table are written to `/tmp/shots/add-prompt-[STEP].png` and transferred via SCP.
- **Report Contents**:
  - `status.json`: Test execution verdict and mutation round-trip latency.
  - `screenshot-add-modal.png`: Filled single prompt modal.
  - `screenshot-optimistic-row.png`: Table showing `tr.dg-row-pending`.
  - `screenshot-saved-state.png`: Table post-settlement with `.dg-save-chip.saved`.
