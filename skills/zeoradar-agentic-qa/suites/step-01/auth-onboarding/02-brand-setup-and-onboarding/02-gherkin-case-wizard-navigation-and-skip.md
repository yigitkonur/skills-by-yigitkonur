# Test Case: 5-Step Guided Walkthrough Navigation, Dot Stepper & Skip Action

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-02-WIZARD-NAVIGATION`
- **Purpose:** Validate linear and backward navigation across the 5 guided onboarding wizard steps (`activeStep === 1..5`), synchronization of header indicator dots (`.zr-step-dots.ob-step-dots`), back button behavior, and execution of "Skip walkthrough" (`window.skipOnboardingWalkthrough()`) routing to the main dashboard.

---

## 2. Tester Brief
The tester loads `/#/onboarding` and begins on Step 1 (Welcome Screen). The tester clicks the primary CTA to advance through Step 2 (Daily Analysis Demo), Step 3 (Geographic Targeting & Engine Profiles), Step 4 (Topic Discovery), and Step 5 (Suggestion Review). At each step, the tester verifies that the top step kicker and header indicator dots accurately reflect the step number. The tester clicks the back button to confirm state retention on reverse navigation. Finally, the tester tests clicking "Skip walkthrough" to assert clean exit to `/#/`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** `window.state.onboarding.activeStep === 1`, valid seed or default workspace
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[CURRENT_STEP]`: Active step integer (1 to 5)

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Framework - Step Navigation and Skip Walkthrough

  Background:
    Given the user is on the onboarding wizard at "[APP_URL]/#/onboarding"
    And the wizard canvas has class "onboarding-step-1"
    And "window.state.onboarding.activeStep" is 1

  @sanity @navigation
  Scenario: Advancing sequentially updates step indicator dots and header kicker
    When the user clicks "button.ob-welcome-cta" ("Get started →")
    Then the active step should become 2
    And the kicker ".ob-step-kicker" should display "STEP 2 OF 5 · DAILY ANALYSIS"
    And the second indicator dot ".ob-step-dot:nth-child(2)" should have class "on"
    When the user clicks the continue button "button.ob-primary-btn.ob-action-grow"
    Then the active step should become 3
    And the third indicator dot ".ob-step-dot:nth-child(3)" should have class "on"

  @positive @navigation @back-button
  Scenario: Back button navigates to previous step without losing entered state
    Given the user is on Step 3 with custom brand name "[BRAND]" entered
    When the user clicks the back button "button.ob-secondary-btn"
    Then the active step should revert to 2
    And the canvas should acquire class "onboarding-step-2"
    When the user clicks continue to return to Step 3
    Then the brand input "#ob-brand-input" should still hold "[BRAND]"

  @positive @skip-action
  Scenario: Skip walkthrough button closes wizard and routes to main app
    Given the user is on any step of the onboarding wizard
    When the user clicks the "Skip walkthrough" button "button.ob-skip-btn"
    Then "window.skipOnboardingWalkthrough()" should execute
    And the onboarding overlay should be dismissed
    And the application router should transition to "[APP_URL]/#/"
```

---

## 5. Visual Checks
- **Header Bar & Indicator Dots:**
  - Top bar `.ob-step-header-bar` contains brand tag, language toggle, 5 indicator dots, and "Skip walkthrough" link.
  - Active dot `.ob-step-dot.on` has filled background and slight expansion.
- **Card Transitions:**
  - Forward navigation triggers CSS transition `.ob-step-enter` for smooth horizontal slide.
- **Step Kickers:**
  - Step 2: `"STEP 2 OF 5 · DAILY ANALYSIS"`.
  - Step 3: `"STEP 3 OF 5 · TARGET AUDIENCE & ENGINES"`.
  - Step 4: `"STEP 4 OF 5 · TOPIC SELECTION"`.
  - Step 5: `"STEP 5 OF 5 · REVIEW PROMPTS"`.

---

## 6. Data & Network Checks
- **State Property Assertion:**
  ```javascript
  const ob = window.state.onboarding;
  assert(ob.activeStep >= 1 && ob.activeStep <= 5);
  ```
- **Skip Action Logic (`assets/onboarding.js:3015`):**
  ```javascript
  window.skipOnboardingWalkthrough();
  assert(window.location.hash === '#/' || window.location.hash === '');
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `02-gherkin-result-case-wizard-navigation-and-skip/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, step transition latency, dot synchronization verification.
  - `evidence.json`: Snapshots of `state.onboarding.activeStep` at each step.
  - `screenshots/01-step-1-welcome.png`: Step 1 hero dialog.
  - `screenshots/02-step-2-daily-demo.png`: Step 2 daily analysis demo card.
  - `screenshots/03-step-3-targeting.png`: Step 3 targeting view.
  - `screenshots/04-skip-dashboard-landing.png`: Main dashboard post-skip.
- **MacBook Execution Protocol:** Ego Browser captures step renders on MacBook; screenshots downloaded via SCP.
