# Test Case 08: On-Demand Run Preview Calculation & Pre-flight Insufficient Credits Gating

## 1. Case ID and Purpose
- **Case ID**: `TC-PLIST-08-RUN-CREDIT-GATING`
- **Purpose**: Verify that the On-Demand Measurement Run trigger (`assets/run-now.js`, `data-action="rn-open"`) fetches the authoritative `runPlanPreview`, computes cell execution costs under the strict 1 credit = 1 planned cell formula, and executes pre-flight credit validation, blocking execution and displaying the actionable billing error when workspace credits are insufficient.

---

## 2. Tester Brief
The tester will:
1. Navigate to the Overview Cockpit at `[APP_URL]/#/[SLUG]/overview`.
2. Locate the "Measurement runs" card (`.card.ov-runs-card`) and click `button[data-action="rn-open"]`.
3. Verify that the Run modal `#modalHolder .modal.rn-modal` opens and renders the plan breakdown:
   - Baseline scope (all active prompts $\times$ active engines).
   - Any active persona incremental scopes.
   - Total planned cells and exact credit cost (`1 credit = 1 cell`).
4. Test the pre-flight credit gate on an account with depleted credits (`[CREDIT_BALANCE] = 0`):
   - Click `button[data-action="rn-start"]`.
   - Verify server returns `{ ok: false, error: { code: "insufficient_credits" } }`.
   - Verify red error message appears: `"The server reports there are not enough credits for this run plan. Buy credits from Billing, then try again."`
   - Confirm that execution is halted and the button stays blocked.
5. Click `button[data-action="rn-close"]` to dismiss the modal cleanly.

---

## 3. Inputs and Prerequisites
- **Target Project**: `[SLUG]` (e.g. `daikin`)
- **Initial Route**: `[APP_URL]/#/[SLUG]/overview`
- **Pre-flight Credit Condition**: Workspace credit balance = `0` (or below required cell cost).
- **Key Selectors**:
  - Open Trigger: `button[data-action="rn-open"]`
  - Modal Window: `#modalHolder .modal.rn-modal`
  - Start Run Button: `button[data-action="rn-start"]`
  - Cancel Button: `button[data-action="rn-close"]`

---

## 4. Gherkin Scenario

```gherkin
Feature: On-Demand Measurement Run Preview & Pre-Flight Credit Gating

  Background:
    Given the tester is authenticated on Zeo Geo-Radar
    And navigates to the Overview Cockpit at "[APP_URL]/#/[SLUG]/overview"
    And the measurement runs card ".card.ov-runs-card" has loaded

  @smoke @run-now @preview
  Scenario Outline: Plan preview calculates total cells and credits under 1-to-1 parity
    When the tester clicks the trigger button "button[data-action='rn-open']"
    Then the run modal "#modalHolder .modal.rn-modal" should appear
    And the preview breakdown should display baseline cells "<BaselineCells>"
    And the total planned execution cells should equal "<TotalCells>"
    And the credit cost in the start button should display "<ExpectedCredits> credits"

    Examples:
      | BaselineCells | TotalCells | ExpectedCredits |
      | 192           | 192        | 192             |
      | 250           | 280        | 280             |
      | 400           | 400        | 400             |

  @billing @error @gating
  Scenario: Pre-flight check blocks execution when workspace credit balance is insufficient
    Given the project workspace has "0" available credits
    When the tester opens the run modal via "button[data-action='rn-open']"
    And clicks the start execution button "button[data-action='rn-start']"
    Then the server should return the error code "insufficient_credits"
    And the modal should render a red error banner containing:
      """
      The server reports there are not enough credits for this run plan. Buy credits from Billing, then try again.
      """
    And the start run action should remain disabled
    When the tester clicks the close button "button[data-action='rn-close']"
    Then the modal dialog should close without dispatching any background worker jobs
```

---

## 5. Visual Checks
1. **Modal Header & Kicker**: Modal renders kicker `.m-kicker` with `"Measurement run"` and heading `"Run measurement now"`.
2. **Breakdown Rows**: `.rank-list` displays items cleanly in flex rows with mono values. Total row is emphasized with bold text.
3. **Red Error Line**: When `d.runError` is populated, the error renders in `div.small.mt8` with `color:var(--red)`.
4. **Action Foot Buttons**: Footer contains neutral "Cancel" button on the left and primary "Start run" button on the right.

---

## 6. Data and Network Checks
1. **Plan Parity Assertion**:
   ```javascript
   const previewData = window.ZeoRunNow._testPreviewData; // or inspected from DOM
   const totalCellsText = document.querySelector('.rn-modal .rank-list .rrow:last-child .val').textContent;
   assert.ok(totalCellsText.includes('cells'), 'Total cells must be stated');
   assert.ok(totalCellsText.includes('credits'), '1 cell = 1 credit equivalence must be stated');
   ```
2. **Pre-flight Error Contract**:
   ```javascript
   const errorContainer = document.querySelector('.rn-modal .dim.small[style*="var(--red)"]');
   assert.ok(errorContainer !== null, 'Red error banner must be present on insufficient credits');
   assert.ok(errorContainer.textContent.includes('insufficient_credits') || errorContainer.textContent.includes('yeterli kredi'), 'Error text must identify credit shortage');
   ```

---

## 7. Evidence and Reporting
- **Matching Result Directory**: `01-gherkin-result-case-on-demand-run-preview-and-credit-gating/`
- **Execution Model Notice**: Ego Browser drives automation on macOS. Modal screenshots are written to `/tmp/shots/run-preview-[STATUS].png` and transferred via SCP to the local results folder.
- **Report Contents**:
  - `status.json`: Execution log and assertion status.
  - `screenshot-run-preview.png`: Plan breakdown and credit estimation.
  - `screenshot-insufficient-credits.png`: Pre-flight billing error banner display.
