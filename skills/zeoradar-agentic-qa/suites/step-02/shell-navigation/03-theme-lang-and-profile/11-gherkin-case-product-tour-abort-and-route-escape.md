# Test Case: Product Tour Mid-Flight Abort (Mask, Close, Skip) and Route Navigation Escape

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-11-TOUR-ABORT-ESCAPE`
- **Purpose:** Verify resilience of the interactive Product Tour against interruptions, ensuring that users can abort the tour mid-flight from any step via the SVG mask backdrop (`svg.tour-mask-svg[data-action="end-tour"]`), the tooltip close button (`button[data-action="end-tour"]`), or the "Skip" button, and assert that route navigation (e.g. browser Back or URL change) dismantles the tour cleanly without leaving dangling spotlight SVG masks or blocking click traps over other views.

---

## 2. Tester Brief
The tester (human or AI agent) will launch the product tour via `startProductTour()`, advance to Step 2, click the tooltip close `✕` button (`.tour-header button[data-action="end-tour"]`), verify that `state.tour.isActive` becomes `false` and `#productTourHolder` is emptied, relaunch the tour to Step 2, click the SVG mask backdrop outside the spotlight ring, verify termination, and finally relaunch the tour and trigger browser navigation to verify that the tour is cleanly unmounted on route exit.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Product tour started on Step 2
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[ABORT_TRIGGER]`: Abort action surface (`close-button`, `mask-click`, `skip-button`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Product Tour - Mid-Flight Abort and Route Navigation Escape

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    When the user initiates the product tour via "startProductTour()"
    And the user advances to step 2 of the tour
    Then "window.state.tour.currentStep" should equal 1
    And the spotlight ring ".tour-spot-ring" should be visible

  @tour @abort @close-button @positive
  Scenario: Clicking the tooltip card close button aborts the tour immediately
    When the user clicks the tour close button ".tour-header button[data-action='end-tour']"
    Then "window.state.tour.isActive" should equal false
    And the container "#productTourHolder" should be empty
    And the spotlight ring ".tour-spot-ring" should be removed from the DOM

  @tour @abort @mask-click @positive
  Scenario: Clicking the SVG mask backdrop aborts the tour immediately
    When the user clicks the SVG backdrop "svg.tour-mask-svg[data-action='end-tour']"
    Then "window.state.tour.isActive" should equal false
    And the container "#productTourHolder" should be empty

  @tour @route-escape @positive
  Scenario: Route navigation while tour is active detaches tour overlay cleanly
    When the user clicks the sidebar item '.side-item[data-key="dashboards"]'
    Then "window.state.tab" should equal "dashboards"
    And "window.state.tour.isActive" should be false
    And the container "#productTourHolder" should be empty
```

---

## 5. Visual Checks
- **Mask Removal:**
  - Darkened SVG mask is removed instantly from `#productTourHolder`.
  - No leftover pointer-events blockers remain over the page.

---

## 6. Data & Network Checks
- **Tour Teardown Assertions:**
  ```javascript
  const holder = document.getElementById('productTourHolder');
  assert(holder.innerHTML.trim() === "", "Tour holder must be completely cleared");
  assert(document.querySelector('.tour-spot-ring') === null, "Spotlight ring must be detached");
  assert(!window.state.tour?.isActive, "state.tour.isActive must be false");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-product-tour-abort-and-route-escape/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of all abort pathways and route escape.
  - `evidence.json`: Captured container HTML length and tour state flags.
  - `screenshots/11-tour-aborted-clean.png`: View showing clean workspace after tour abort.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-11-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
