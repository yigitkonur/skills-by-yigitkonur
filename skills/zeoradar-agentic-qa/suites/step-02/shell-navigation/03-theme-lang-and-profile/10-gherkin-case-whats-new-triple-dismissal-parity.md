# Test Case: What's New Modal Triple-Dismissal Parity (Close Button, Backdrop, Escape) & DOM Cleanliness

## 1. Case ID & Purpose
- **Case ID:** `TC-PREF-10-WHATS-NEW-TRIPLE-DISMISSAL`
- **Purpose:** Verify dismissal parity across the 3 independent dismissal vectors supported by the "What's New" modal (`assets/ui-shell.js` lines 620–625 and `assets/radar.js` lines 3848–3873): clicking the explicit close button, clicking the backdrop overlay (`.overlay[data-action="modal-bg"]`), and pressing the global `Escape` key, ensuring that all 3 pathways empty `#modalHolder` completely and leave zero zombie event hooks or residual overlay DOM nodes.

---

## 2. Tester Brief
The tester (human or AI agent) will open the What's New modal, dismiss it via the overlay backdrop click, verify that `#modalHolder` has 0 children, reopen the modal, dismiss it via the `Escape` key, verify that `#modalHolder` has 0 children, reopen the modal, dismiss it via the explicit close `✕` button (`button.close`), and assert consistent teardown.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** `#modalHolder` empty
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[DISMISSAL_METHOD]`: Method tested (`backdrop-click`, `keyboard-escape`, `button-close`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Modals - What's New Triple-Dismissal Parity and Container Cleanliness

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the modal holder "#modalHolder" is empty

  @modal @dismissal @backdrop @positive
  Scenario: Dismissing What's New modal via backdrop overlay click cleans modalHolder
    When the user clicks the footer button ".foot-btn[data-action='whats-new']"
    Then the modal ".whatsnew-modal" should be visible inside "#modalHolder"
    When the user clicks the modal backdrop ".overlay[data-action='modal-bg']"
    Then the modal ".whatsnew-modal" should be removed from the DOM
    And "#modalHolder" should have exactly 0 children

  @modal @dismissal @escape @positive
  Scenario: Dismissing What's New modal via global Escape key cleans modalHolder
    When the user clicks the footer button ".foot-btn[data-action='whats-new']"
    Then the modal ".whatsnew-modal" should be visible inside "#modalHolder"
    When the user presses the "Escape" key
    Then the modal ".whatsnew-modal" should be removed from the DOM
    And "#modalHolder" should have exactly 0 children

  @modal @dismissal @button @positive
  Scenario: Dismissing What's New modal via top-right close button cleans modalHolder
    When the user clicks the footer button ".foot-btn[data-action='whats-new']"
    Then the modal ".whatsnew-modal" should be visible inside "#modalHolder"
    When the user clicks the modal close button ".whatsnew-modal button.close"
    Then the modal ".whatsnew-modal" should be removed from the DOM
    And "#modalHolder" should have exactly 0 children
```

---

## 5. Visual Checks
- **Clean Teardown:**
  - In all 3 dismissal scenarios, the screen background returns to standard opacity without dark residual scrims.
  - Page interactivity is fully restored.

---

## 6. Data & Network Checks
- **Holder Cleanliness Assertions:**
  ```javascript
  const mh = document.getElementById('modalHolder');
  assert(mh !== null, "#modalHolder must exist");
  assert(mh.children.length === 0, "#modalHolder must have 0 children after dismissal");
  assert(mh.innerHTML.trim() === "", "#modalHolder innerHTML must be empty");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-whats-new-triple-dismissal-parity/`
- **Required Artifacts:**
  - `result.md`: Evaluation log confirming dismissal parity across all 3 vectors.
  - `evidence.json`: Captured container child counts and close hook records.
  - `screenshots/10-modal-dismissed-clean.png`: Screen capture showing clean dashboard after dismissal.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/pref/case-10-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
