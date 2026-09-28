# Test Case: Topic Selection Matrix, Progress Fill & 10-Topic Ceiling

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-07-TOPIC-CEILING-MATRIX`
- **Purpose:** Validate the topic discovery matrix on Step 4 (`.topic-pills-matrix`), dynamic selection counter (`.ob-count-text`), progress bar fill calculation (`(count / 10) * 100`), strict enforcement of the 10-topic maximum selection ceiling, visual application of `.topic-pill-at-cap`, and toast rejection on attempting to select an 11th topic.

---

## 2. Tester Brief
The tester advances to Step 4 of the wizard where generated topic pills are rendered. The tester selects pills incrementally, observing the counter (`"1 / 10 selected"`, `"2 / 10 selected"`, etc.) and the progress bar fill width. When 10 topics are selected, the tester asserts that all remaining unselected topic pills receive class `.topic-pill-at-cap`. The tester then attempts to click an 11th topic pill to confirm that it is rejected and an error toast (`"You can select up to 10 topics"`) is displayed. Finally, the tester deselects one topic and verifies that pills become re-selectable.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** Step 4 (`activeStep === 4`), suggestions generated, `st.maxTopics === 10`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[SELECTED_COUNT]`: Current count of selected topic pills (0 to 10)

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Step 4 - Topic Matrix Selection and Cap Enforcement

  Background:
    Given the user is on Step 4 of the onboarding wizard at "[APP_URL]/#/onboarding"
    And the topic pills matrix ".topic-pills-matrix" displays generated topic suggestions
    And "window.state.onboarding.maxTopics" is configured as 10

  @sanity @selection @counter
  Scenario: Selecting and deselecting topic pills updates counter and progress bar
    When the user toggles 3 topic pills to selected
    Then the selection counter ".ob-count-text" should display "3 / 10 selected"
    And the progress bar fill ".ob-progress-bar-fill" width should equal "30%"
    When the user clicks one of the selected pills to deselect it
    Then the selection counter should update to "2 / 10 selected"
    And the progress bar fill width should decrease to "20%"

  @adversarial @boundary @cap-enforcement
  Scenario: 10-topic ceiling blocks 11th selection and styles remaining pills
    Given the user has selected exactly 10 topic pills
    Then the selection counter should display "10 / 10 selected"
    And the progress bar fill width should be "100%"
    And all unselected topic pills in the matrix should have class "topic-pill-at-cap"
    When the user clicks any unselected topic pill
    Then the pill should NOT acquire class "topic-pill-selected"
    And the selected count should remain 10
    And an error toast should appear containing:
      """
      You can select up to 10 topics
      """

  @positive @recovery
  Scenario: Deselecting a pill releases the cap and restores interactivity
    Given the user is at the 10-topic capacity
    When the user deselects one active topic pill
    Then the selected count should drop to 9
    And the class "topic-pill-at-cap" should be removed from unselected pills
    And unselected pills should become clickable again
```

---

## 5. Visual Checks
- **Topic Pills Matrix:**
  - Responsive flex/grid wrapping topic pills with 8px gap.
  - Selected pills: filled brand background (`var(--color-primary, #0ea5e9)`), white text, check icon.
  - At-capacity pills (`.topic-pill-at-cap`): reduced opacity (0.45), `cursor: not-allowed`.
- **Progress Bar:**
  - Element `.ob-progress-bar-bg` has `.ob-progress-bar-fill` with smooth width transitions (`transition: width 0.25s ease`).

---

## 6. Data & Network Checks
- **Selection Gating Logic (`assets/onboarding.js:1301` & `3133`):**
  ```javascript
  const st = window.state.onboarding;
  const count = (typeof obSelectedTopicNames === 'function') ? obSelectedTopicNames(st.live).length : 10;
  assert(count <= st.maxTopics, "Selected count must never exceed maxTopics (10)");
  ```
- **Toast Invocation:**
  - Invokes `showOnboardingToast(t("You can select up to 10 topics...", "..."), "error")`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `07-gherkin-result-case-topic-matrix-selection-and-ceiling/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, topic count assertion trace, cap rejection log.
  - `evidence.json`: Array of selected topic IDs and capacity state flags.
  - `screenshots/01-topics-partially-selected.png`: 4 of 10 selected with 40% progress bar.
  - `screenshots/02-topics-at-capacity.png`: 10 of 10 selected with `.topic-pill-at-cap` on remaining pills.
  - `screenshots/03-topics-cap-toast-rejection.png`: Error toast on attempting 11th topic.
- **MacBook Execution Protocol:** Ego Browser interacts with topic pill elements on MacBook; visual captures downloaded via SCP.
