# Test Case: Wizard Form Gating, Step Jump Blocking & Zero-Selection Guardrails

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-12-GATING-GUARDRAILS`
- **Purpose:** Validate form guardrails, input gating, step jump prevention when prerequisites are missing (blank brand or domain preventing jump to Step 4), zero-topic selection gating preventing advance to Step 5, and zero-prompt selection gating disabling the finalize CTA and blocking execution modal display with toast error `"Select at least one prompt before continuing."`.

---

## 2. Tester Brief
The tester evaluates boundary integrity and adversarial inputs across the wizard. First, on Step 3, leave brand and domain blank, and attempt to jump to Step 4 via `setOnboardingStep(4)` or clicking the Step 4 dot; verify that the transition is blocked and error toast `"Enter your brand name and domain first."` is displayed. Second, on Step 4, deselect all topic pills and verify that the continue button is disabled. Third, on Step 5, deselect all prompt rows and verify that the finalize button is disabled and direct modal invocation is blocked with toast `"Select at least one prompt before continuing."`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** Various wizard steps under test
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Guardrails - Prerequisite Gating and Zero-Selection Prevention

  @negative @gating @step-jump
  Scenario: Step 4 is blocked when brand and domain fields are blank
    Given the user is on Step 3 of the onboarding wizard at "[APP_URL]/#/onboarding"
    And the brand input "#ob-brand-input" is empty
    And the domain input "#ob-domain-input" is empty
    When the user attempts to jump to Step 4 by clicking the Step 4 indicator dot
    Then an error toast should appear displaying:
      """
      Enter your brand name and domain first.
      """
    And the active step should remain 3
    And the canvas should remain on "onboarding-step-3"

  @negative @gating @zero-topics
  Scenario: Advancing to Step 5 is disabled when zero topics are selected
    Given the user is on Step 4 of the onboarding wizard
    When the user deselects all topic pills in the matrix
    Then the selection counter should display "0 / 10 selected"
    And the continue button "button.ob-primary-btn.ob-action-grow" should be disabled
    When the user clicks the disabled continue button
    Then no transition to Step 5 should occur

  @negative @gating @zero-prompts
  Scenario: Opening execution modal is blocked when zero prompts are selected
    Given the user is on Step 5 of the onboarding wizard
    When the user deselects every prompt row in the accordion
    Then the total prompts badge ".ob-total-prompts-badge strong" should display "0"
    And the finalize button "button.ob-prompts-continue" should have attribute "disabled"
    When the user attempts to trigger "window.openExecutionModal()" directly
    Then the modal ".ob-exec-modal" should NOT open
    And an error toast should appear displaying:
      """
      Select at least one prompt before continuing.
      """
```

---

## 5. Visual Checks
- **Disabled Button States:**
  - Step 4 CTA: Opacity 0.5, `cursor: not-allowed` when `selectedTopicCount === 0`.
  - Step 5 Finalize CTA: Opacity 0.5, `cursor: not-allowed` when `totalPrompts === 0`.
- **Toast Notifications:**
  - Error toast rendered with icon `icon('warning')`, red accent bar, auto-dismissing after 3.5 seconds.

---

## 6. Data & Network Checks
- **Step Gating Logic (`assets/onboarding.js`):**
  ```javascript
  // setOnboardingStep gating check
  if (targetStep >= 4 && (!lv.form.brand || !lv.form.domain)) {
    showOnboardingToast(t("Enter your brand name and domain first.", "Önce marka adınızı ve alan adınızı girin."), "error");
    return; // Halt navigation
  }
  ```
- **Modal Gating Check (`assets/onboarding.js:3332`):**
  ```javascript
  window.openExecutionModal = function () {
    var totalPrompts = obSelectedPromptsCount();
    if (totalPrompts === 0) {
      showOnboardingToast(t("Select at least one prompt before continuing.", "Devam etmeden önce en az bir prompt seçin."), "error");
      return;
    }
    // ... opens modal
  };
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `12-gherkin-result-case-onboarding-gating-and-guardrails/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, guardrail validation trace, toast copy verification.
  - `evidence.json`: State snapshot of activeStep, topic counts, and prompt counts during blocked attempts.
  - `screenshots/01-step-jump-blocked-toast.png`: Error toast on blank brand/domain jump.
  - `screenshots/02-zero-topics-disabled-cta.png`: Step 4 with 0 topics selected and disabled button.
  - `screenshots/03-zero-prompts-blocked-toast.png`: Step 5 zero prompts gating error toast.
- **MacBook Execution Protocol:** Ego Browser attempts invalid step transitions on MacBook; logs and screenshots downloaded via SCP.
