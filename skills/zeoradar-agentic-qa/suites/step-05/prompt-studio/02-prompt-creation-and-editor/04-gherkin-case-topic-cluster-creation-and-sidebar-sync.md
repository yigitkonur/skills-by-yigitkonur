# Test Case 04: Taxonomy Topic Creation Modal & Sidebar Cluster Synchronization

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-04-TOPIC-CREATION`
- **Purpose**: Verify that creating a new taxonomy topic via the modal dialog (`add-topic`) validates input non-emptiness, dispatches the authoritative `upsert-topic` command, and immediately synchronizes the new topic cluster into the taxonomy sidebar (`.dg-side`) and modal dropdown selectors with initial prompt count `0`.

---

## 2. Tester Brief
The tester will:
1. Open the Prompt Designer Workbench for `[DOMAIN]`.
2. Click the topic creation button `button[data-action="dg-open-add-topic"]` in the sidebar.
3. Verify that the modal opens with title `"Add Topic"` (`"Konu Ekle"`) and input `#newTopicInput`.
4. Attempt to submit with an empty string and verify validation prevents creation.
5. Enter a new topic title: `[TOPIC_NAME]` (e.g. `"[TOPIC_NAME]"`).
6. Click submit button `button[data-action="apply-bulk-modal"][data-type="add-topic"]`.
7. Verify that:
   - Command `upsert-topic` is dispatched.
   - The modal closes.
   - The new topic row `.t-row` appears in `.dg-side` with initial count badge `0`.
   - Opening the Add Prompt modal includes `[TOPIC_NAME]` as a selectable option in `#dgPromptTopic`.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Form Selectors**:
  - Add Topic Trigger: `button.btn.small.addt[data-action="dg-open-add-topic"]`
  - Topic Input: `input#newTopicInput.wizard-input`
  - Submit Button: `button[data-action="apply-bulk-modal"][data-type="add-topic"]`
- **New Topic Name**: `"[TOPIC_NAME]"`

---

## 4. Gherkin Scenario

```gherkin
Feature: Taxonomy Topic Cluster Creation & Synchronization

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And the page has mounted with selector ".designer-grid"

  @smoke @topic @modal
  Scenario: Create new topic cluster and verify immediate sidebar synchronization
    When the tester clicks the add topic button "button[data-action='dg-open-add-topic']"
    Then the modal overlay ".overlay.dg-modal-root" should appear
    And the modal title should display "Add Topic"
    When the tester enters "[TOPIC_NAME]" into "input#newTopicInput"
    And clicks the submit button "button[data-action='apply-bulk-modal'][data-type='add-topic']"
    Then the command "upsert-topic" should be dispatched to the server
    And the modal dialog should close
    And the sidebar ".dg-side" should display the new topic row "[TOPIC_NAME]"
    And the new topic count badge ".n" should equal "0"
    When the tester opens the Add Prompt modal via "button[data-action='dg-open-add-prompt']"
    Then the topic selector "select#dgPromptTopic" should include "[TOPIC_NAME]"
```

---

## 5. Visual Checks
1. **Add Topic Modal**: Compact modal frame (`.wizard-sm`) with clear single text input and cancel/submit actions.
2. **Sidebar Addition**: New `.t-row` appends smoothly to the topic list with count pill `.n` containing `"0"`.
3. **Dropdown Inclusion**: `<option>` with label `"[TOPIC_NAME]"` appears in `#dgPromptTopic`.

---

## 6. Data and Network Checks
1. **Command Payload Check**:
   - Verify `upsert-topic` call carries `{ projectId: "[PROJECT_ID]", label: "[TOPIC_NAME]" }`.
2. **Sidebar DOM Integrity**:
   ```javascript
   const topicRows = Array.from(document.querySelectorAll('.dg-side .t-row span:first-child'));
   const found = topicRows.some(el => el.textContent.includes('[TOPIC_NAME]'));
   assert.ok(found, 'New topic must be rendered in the sidebar taxonomy');
   ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-topic-cluster-creation-and-sidebar-sync/`
- **Execution Model Notice**: Automated via Ego Browser on macOS. Screenshots of modal and updated sidebar are written to `/tmp/shots/topic-sync-[STEP].png` and pulled via SCP.
- **Report Contents**:
  - `status.json`: Test execution log and command roundtrip timing.
  - `screenshot-add-topic-modal.png`: Open Add Topic modal.
  - `screenshot-sidebar-synced.png`: Sidebar reflecting new cluster with `0` badge.
