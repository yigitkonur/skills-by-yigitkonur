# Test Case 02: Input Validation Gating, Whitespace-Only String & Missing Topic Rejection

## 1. Case ID and Purpose
- **Case ID**: `TC-PCREAT-02-VALIDATION-GATING`
- **Purpose**: Verify that the prompt creation modal strictly executes client-side pre-flight validation, rejecting empty strings, whitespace-only queries (`replace(/^\s+|\s+$/g, '')`), and unassigned topic selectors with actionable toast warnings while dispatching zero server mutations.

---

## 2. Tester Brief
The tester will:
1. Open the Add Prompt modal via `button[data-action="dg-open-add-prompt"]`.
2. Leave the query input `#dgPromptText` empty and click the submit button.
3. Assert that:
   - Submission is blocked.
   - The modal remains open.
   - A warning toast appears stating `"Enter the prompt text."` (Turkish: `"Prompt metnini girin."`).
   - Zero network requests are sent.
4. Enter whitespace characters only (spaces, tabs, newlines) into `#dgPromptText` and submit.
5. Confirm the trimming check fails and displays `"Enter the prompt text."`.
6. Enter valid text but leave the topic selector `#dgPromptTopic` empty or unselected.
7. Click submit and verify toast warning `"Add a topic first."` (Turkish: `"Önce bir konu ekleyin."`).

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/prompts?workspace=designer`
- **Validation Test Inputs**:
  - Empty: `""`
  - Whitespace: `"   "`, `"\t  \n "`
  - Valid Query: `"Luxury gift boxes for holidays"`
  - Empty Topic: `""`

---

## 4. Gherkin Scenario

```gherkin
Feature: Prompt Creation Input Validation & Whitespace Gating

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Prompt Designer Workbench at "[APP_URL]/#/[SLUG]/prompts?workspace=designer"
    And opens the Add Prompt modal dialog

  @validation @smoke
  Scenario Outline: Reject empty and whitespace-only query strings
    When the tester inputs "<WhitespaceInput>" into the prompt text field "input#dgPromptText"
    And clicks the submit button "button[data-action='apply-bulk-modal'][data-type='add-prompt']"
    Then the modal dialog should remain visible
    And a warning toast should appear displaying "Enter the prompt text."
    And no "upsert-prompt" command should be dispatched to the server

    Examples:
      | WhitespaceInput |
      |                 |
      |                 |
      |       \t        |

  @validation @topic-gate
  Scenario: Reject prompt creation when no category topic is selected
    Given the tester enters "Valid HVAC inverter climate prompt query" into "input#dgPromptText"
    When the tester clears or leaves the topic selector "select#dgPromptTopic" unselected
    And clicks the submit button "button[data-action='apply-bulk-modal'][data-type='add-prompt']"
    Then the modal dialog should remain visible
    And a warning toast should appear displaying "Add a topic first."
    And no "upsert-prompt" command should be dispatched to the server
```

---

## 5. Visual Checks
1. **Modal Retention**: The modal frame `.zr-wizard.wizard-frame` remains mounted and focused when validation fails.
2. **Toast Notification**: Toast appears docked at top/center of screen with warning styling (amber/red accent) and self-dismisses after 3 seconds.
3. **Form Integrity**: Previously entered valid fields (country, locale, type) are preserved without reset upon validation failure.

---

## 6. Data and Network Checks
1. **Zero-Mutation Invariant**:
   ```javascript
   // Listen to network dispatcher during validation attempt
   let mutationSent = false;
   const originalCallCommand = window.ZEO_DATA_PROVIDER.callCommand;
   window.ZEO_DATA_PROVIDER.callCommand = function(cmd) {
     if (cmd === 'upsert-prompt') mutationSent = true;
     return originalCallCommand.apply(this, arguments);
   };
   // Click submit with empty input
   document.querySelector('button[data-action="apply-bulk-modal"][data-type="add-prompt"]').click();
   assert.strictEqual(mutationSent, false, 'Validation failure must not dispatch server command');
   ```
2. **Validation Logic Audit**:
   ```javascript
   const inputVal = "   \t  ";
   const trimmed = inputVal.replace(/^\s+|\s+$/g, '');
   assert.strictEqual(trimmed.length, 0, 'Whitespace string must trim to length 0');
   ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-prompt-form-validation-and-whitespace-gating/`
- **Execution Model Notice**: Remote automation runs via Ego Browser on macOS. Screenshots of validation toast alerts are captured to `/tmp/shots/validation-gate-[TYPE].png` and pulled via SCP.
- **Report Contents**:
  - `status.json`: Test execution log.
  - `screenshot-empty-text-toast.png`: Warning toast on empty text submission.
  - `screenshot-whitespace-toast.png`: Warning toast on whitespace submission.
  - `screenshot-missing-topic-toast.png`: Warning toast on unassigned topic submission.
