# Test Case: Interactive 4-Step Product Tour Walkthrough, Spotlight Cutout Rings & Stepper

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-05-PRODUCT-TOUR-WALKTHROUGH`
- **Purpose:** Verify the complete interactive 4-step Product Tour journey (`assets/radar.js` lines 6580–6740), ensuring that initiating the tour mounts an SVG spotlight cutout mask (`svg.tour-mask-svg`) in `#productTourHolder`, highlights the target sidebar controls through dynamic coordinate cutouts, advances sequentially from Step 1 to Step 4, displays the correct step badge counter (`"Step {n} / 4"`), and completes cleanly on clicking `"Enter Platform"`.

---

## 2. Tester Brief
The tester (human or AI agent) will invoke `startProductTour()`, verify that `#productTourHolder` displays the SVG overlay and the Step 1 card pointing to Answer Engine Insights (`.side-item[data-key="aei"]`), click `"Next Step →"` to advance through Step 2 (Pages), Step 3 (Prompts), and Step 4 (Opportunities), assert that the final button text reflects `"Enter Platform"`, click it, and assert that the tour finishes and `#productTourHolder` is emptied.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Tour not active (`state.tour` uninitialized or inactive)
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[STEP_INDEX]`: Zero-based step index (0 to 3)
  - `[TARGET_SELECTOR]`: Spotlight target element selector

---

## 4. Gherkin Scenario

```gherkin
Feature: Product Tour - Complete 4-Step Interactive Walkthrough

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the product tour container "#productTourHolder" is empty

  @tour @onboarding @spotlight @positive
  Scenario: Walking through all 4 tour steps highlights target elements and finishes cleanly
    When the user initiates the product tour via "startProductTour()"
    Then "window.state.tour.isActive" should equal true
    And "window.state.tour.currentStep" should equal 0
    And the spotlight ring ".tour-spot-ring" should align with target '.side-item[data-key="aei"]'
    And the tour badge ".tour-step-badge" should contain "1"

    When the user clicks the next tour button ".tour-footer button[data-action='next-tour-step']"
    Then "window.state.tour.currentStep" should equal 1
    And the tour badge ".tour-step-badge" should contain "2"

    When the user clicks the next tour button ".tour-footer button[data-action='next-tour-step']"
    Then "window.state.tour.currentStep" should equal 2
    And the tour badge ".tour-step-badge" should contain "3"

    When the user clicks the next tour button ".tour-footer button[data-action='next-tour-step']"
    Then "window.state.tour.currentStep" should equal 3
    And the tour badge ".tour-step-badge" should contain "4"
    And the tour action button should display "Enter Platform"

    When the user clicks the final tour button ".tour-footer button[data-action='next-tour-step']"
    Then "window.state.tour.isActive" should equal false
    And the container "#productTourHolder" should be empty
```

---

## 5. Visual Checks
- **Spotlight Masking:**
  - Entire screen is darkened except for the transparent cutout rectangle around the active sidebar item.
  - Active spotlight ring pulses gently around the target item.
  - Tooltip card `.tour-tooltip-card` is positioned alongside the spotlight without overflowing off-screen.

---

## 6. Data & Network Checks
- **State Invariants:**
  ```javascript
  const tour = window.state.tour;
  assert(tour && tour.currentStep === 3, "Final step must equal 3");
  // After finishing:
  assert(!window.state.tour?.isActive, "Tour must be inactive after completion");
  assert(document.getElementById('productTourHolder').innerHTML === "", "Holder must be emptied");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-product-tour-complete-walkthrough/`
- **Required Artifacts:**
  - `result.md`: Evaluation log covering all 4 steps, step counter text, and final completion.
  - `evidence.json`: Step coordinate dumps and state transitions.
  - `screenshots/05-tour-step-1.png`: Step 1 highlighting Answer Engine Insights.
  - `screenshots/05-tour-step-4.png`: Step 4 showing Enter Platform button.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-05-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
