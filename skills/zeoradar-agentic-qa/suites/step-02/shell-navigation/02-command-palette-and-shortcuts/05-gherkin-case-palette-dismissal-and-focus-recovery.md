# Test Case: Palette Dismissal via Escape & Backdrop with Two-Tier Focus Recovery

## 1. Case ID & Purpose
- **Case ID:** `TC-CMD-05-DISMISSAL-FOCUS-RECOVERY`
- **Purpose:** Verify the dual dismissal vectors for the Command Palette (pressing `Escape` and clicking the outer backdrop `#cmdPaletteModal.cmd-backdrop`) and assert the two-tier focus recovery contract: ensuring that when dismissed, focus is accurately returned to `state.commandPalette.previousActiveElement`, or falls back gracefully to active modal containers if the prior element was unmounted.

---

## 2. Tester Brief
The tester (human or AI agent) will focus an interactive element on the page (e.g. a sidebar button or input), open the command palette, assert that `previousActiveElement` is recorded in state, press `Escape`, verify that the palette closes and focus returns to the original button, reopen the palette, click the darkened backdrop outside `.cmd-modal`, and verify that the palette closes with focus returned safely.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** User focused on interactive element `.foot-btn[data-action="whats-new"]`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[FOCUSED_ELEMENT]`: Selector of element focused prior to palette launch

---

## 4. Gherkin Scenario

```gherkin
Feature: Command Palette - Dismissal Vectors and Two-Tier Focus Restoration

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the user focuses the element ".foot-btn[data-action='whats-new']"

  @dismissal @escape @focus @positive
  Scenario: Pressing Escape closes the command palette and restores previous focus
    When the user presses the shortcut "Meta+K"
    Then the command palette modal "#cmdPaletteModal" should be open
    And "window.state.commandPalette.previousActiveElement" should not be null
    When the user presses the "Escape" key
    Then the command palette modal "#cmdPaletteModal" should be removed from the DOM
    And "window.state.commandPalette.isOpen" should equal false
    And the document active element should be the original element ".foot-btn[data-action='whats-new']"

  @dismissal @backdrop @focus @positive
  Scenario: Clicking the backdrop dismisses the palette and restores previous focus
    Given the user focuses the element ".foot-btn[data-action='whats-new']"
    When the user presses the shortcut "Meta+K"
    Then the command palette modal "#cmdPaletteModal" should be open
    When the user clicks the outer backdrop "#cmdPaletteModal"
    Then the command palette modal "#cmdPaletteModal" should be removed from the DOM
    And "window.state.commandPalette.isOpen" should equal false
    And the document active element should be the original element ".foot-btn[data-action='whats-new']"
```

---

## 5. Visual Checks
- **Backdrop Click Seam:**
  - Clicking inside `.cmd-modal` does NOT close the palette (`stopPropagation` check).
  - Clicking on the tinted backdrop outside `.cmd-modal` closes the palette instantly.
- **Focus Ring Return:**
  - The focus ring or outline returns visibly to the previously focused button.

---

## 6. Data & Network Checks
- **Focus Restoration Assertions:**
  ```javascript
  const prev = window.state.commandPalette.previousActiveElement;
  assert(document.getElementById('cmdPaletteModal') === null, "Palette must be unmounted");
  assert(document.activeElement === prev, "Focus must be restored to previous active element");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-palette-dismissal-and-focus-recovery/`
- **Required Artifacts:**
  - `result.md`: Detailed trace of focus acquisition, storage, and recovery after dismissal.
  - `evidence.json`: Captured activeElement tags and attributes.
  - `screenshots/05-focus-restored.png`: View showing restored focus ring on button.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/cmd/case-05-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
