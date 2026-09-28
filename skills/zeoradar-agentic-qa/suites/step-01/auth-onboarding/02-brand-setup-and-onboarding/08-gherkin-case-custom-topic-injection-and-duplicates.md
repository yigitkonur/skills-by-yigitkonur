# Test Case: Custom Topic Inline Creation, Duplicate Prevention & Regeneration

## 1. Case ID & Purpose
- **Case ID:** `TC-ONB-08-CUSTOM-TOPIC-DUPLICATE`
- **Purpose:** Validate the inline custom topic creation interface (`button.topic-pill-add`, `#custom-topic-input`), prevent insertion of duplicate topics (case-insensitive deduplication via `obTopicKey`), verify appearance of the custom topic pill in the active selection, and assert display of the topic regeneration note (`.ob-topic-regen-note`).

---

## 2. Tester Brief
The tester opens Step 4 and clicks the "Add custom" topic button. The tester tests typing an existing topic name (case-insensitively, e.g. `"RESPONSIVE WEB APP UI/UX"`) and attempting to save it. The tester asserts that the duplicate is rejected with toast `"That topic is already in the list."` and the topic list count does not increase. Next, the tester enters a brand-new custom topic (e.g. `"[CUSTOM_TOPIC]"`), saves it, asserts that the new pill is created and automatically selected, and verifies that `.ob-topic-regen-note` appears with a button to regenerate suggestions.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/onboarding`
- **Prerequisite State:** Step 4 (`activeStep === 4`), fewer than 10 topics selected
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[EXISTING_TOPIC]`: Pre-populated topic (`"Responsive web app UI/UX"`)
  - `[CUSTOM_TOPIC]`: Unique custom topic (`"[CUSTOM_TOPIC]"`, e.g. `"Isı Pompası Çözümleri"`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Onboarding Step 4 - Custom Topic Creation and Duplicate Prevention

  Background:
    Given the user is on Step 4 of the onboarding wizard at "[APP_URL]/#/onboarding"
    And the topic pills matrix contains existing generated topics
    And the selected topic count is less than 10

  @negative @deduplication @toast
  Scenario: Adding a duplicate custom topic is rejected case-insensitively
    When the user clicks the "Add custom" button "button.topic-pill.topic-pill-add"
    Then the inline input "#custom-topic-input" should be displayed and focused
    When the user types "[EXISTING_TOPIC]" with varied casing into "#custom-topic-input"
    And clicks the save check button ".ob-action-check" or presses Enter
    Then an error toast should appear displaying:
      """
      That topic is already in the list.
      """
    And the duplicate topic should NOT be added to "live.tp.items" or "state.topics"
    And the selected topic count should remain unchanged

  @positive @custom-creation @regeneration
  Scenario: Adding a unique custom topic adds selected pill and shows regeneration note
    When the user clicks the "Add custom" button "button.topic-pill.topic-pill-add"
    And types "[CUSTOM_TOPIC]" into "#custom-topic-input"
    And clicks the save check button ".ob-action-check"
    Then a success toast "Custom topic added." should appear
    And a new topic pill for "[CUSTOM_TOPIC]" should appear in the matrix with class "topic-pill-selected"
    And the regeneration notice container ".ob-topic-regen-note" should become visible
    And the button "button[data-action='ob-regen-topics']" should be rendered to regenerate prompts
```

---

## 5. Visual Checks
- **Inline Custom Input Styling:**
  - Pill converts to an editable input box with height 32px, rounded pill border, and inline check `✓` (`.ob-action-check`) and cancel `✕` (`.ob-action-cancel`) action buttons.
  - Pressing `Escape` or clicking cancel reverts to the "Add custom" button without changes.
- **Regeneration Banner:**
  - Banner `.ob-topic-regen-note` features a soft info accent border, helper copy explaining that custom topics require fresh prompt fanout, and an outline action button.

---

## 6. Data & Network Checks
- **Deduplication Key Logic (`assets/onboarding.js:3195`):**
  ```javascript
  const key1 = obTopicKey("[CUSTOM_TOPIC]");
  const key2 = obTopicKey("[CUSTOM_TOPIC]".toLowerCase());
  assert(key1 === key2, "obTopicKey must normalize whitespace and casing");
  ```
- **State Properties:**
  ```javascript
  const lv = window.state.onboarding.live;
  assert(lv.tp.custom.includes('[CUSTOM_TOPIC]'), "Custom topics must be tracked in lv.tp.custom");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `08-gherkin-result-case-custom-topic-injection-and-duplicates/`
- **Required Artifacts:**
  - `result.md`: Pass/Fail status, deduplication test log, custom topic state trace.
  - `evidence.json`: Array of custom topics and key normalization values.
  - `screenshots/01-custom-topic-inline-input.png`: Active inline input box.
  - `screenshots/02-custom-topic-duplicate-toast.png`: Error toast on duplicate topic entry.
  - `screenshots/03-custom-topic-added-regen-note.png`: New custom pill and regeneration banner.
- **MacBook Execution Protocol:** Ego Browser interacts with custom topic elements on MacBook; visual logs downloaded via SCP.
