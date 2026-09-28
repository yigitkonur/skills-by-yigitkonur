# Test Case: What's New Feature Announcement Modal Content Schema and Feature List

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-04-WHATS-NEW-MODAL`
- **Purpose:** Verify the "What's New" feature announcement modal (`assets/radar.js` lines 3848–3873), ensuring that clicking `.foot-btn[data-action="whats-new"]` renders `.modal.whatsnew-modal` inside `#modalHolder`, displays the 4 core capability cards with their respective icons, titles, and descriptions, and supports dismissal via the primary confirmation button (`button[data-action="modal-close"]`).

---

## 2. Tester Brief
The tester (human or AI agent) will click the gift icon button in the sidebar footer (`.foot-btn[data-action="whats-new"]`), assert that `.whatsnew-modal` mounts in `#modalHolder`, verify that exactly 4 feature announcement items (`.wn-item`) are rendered with proper iconography and copy, click the primary confirmation button (`"Got it"` / `"Anladım"`), and assert that the modal closes cleanly.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** `#modalHolder` empty
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[FEATURE_TITLE]`: Expected capability titles in English and Turkish

---

## 4. Gherkin Scenario

```gherkin
Feature: Preferences - What's New Feature Announcement Modal

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the modal container "#modalHolder" is empty

  @whats-new @modal @positive
  Scenario: Opening What's New modal displays 4 core capability announcements
    When the user clicks the footer button ".foot-btn[data-action='whats-new']"
    Then the modal element ".whatsnew-modal" should be mounted inside "#modalHolder"
    And the feature announcement items ".wn-item" count should equal 4
    And the modal should contain the following capability titles:
      | Citation Network Graph |
      | Date Range Picker      |
      | Watched Pages          |
      | AEO Content Studio     |
    When the user clicks the modal confirmation button ".whatsnew-modal button[data-action='modal-close']"
    Then the modal element ".whatsnew-modal" should be removed from "#modalHolder"
    And "#modalHolder" should have 0 children
```

---

## 5. Visual Checks
- **Modal Typography & Icons:**
  - Kicker tag reads `"WHAT'S NEW"` / `"YENİLİKLER"`.
  - Feature items render distinct icons: `link`, `calendar`, `bookmark`, `sparkle`.
  - Confirmation button is styled with high contrast (`button.black`).

---

## 6. Data & Network Checks
- **DOM Assertions:**
  ```javascript
  const modal = document.querySelector('.whatsnew-modal');
  const items = document.querySelectorAll('.wn-item');
  assert(modal !== null, "Whats New modal must be open");
  assert(items.length === 4, "Must render exactly 4 capability items");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-whats-new-feature-announcements/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of feature announcement schema and modal lifecycle.
  - `evidence.json`: Captured item titles, descriptions, and container states.
  - `screenshots/04-whats-new-modal-open.png`: View of the opened What's New announcement modal.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-04-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
