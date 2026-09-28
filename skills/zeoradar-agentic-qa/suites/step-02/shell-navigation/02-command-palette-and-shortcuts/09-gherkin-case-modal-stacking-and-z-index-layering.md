# Test Case: Layered Modal Stacking over Active Dialogs and Focus Preservation

## 1. Case ID & Purpose
- **Case ID:** `TC-CMD-09-MODAL-STACKING-ZINDEX`
- **Purpose:** Verify modal stacking and z-index hierarchy when the Command Palette is opened while an existing modal or live drawer is already active inside `#modalHolder` (e.g. What's New modal), ensuring that `#cmdPaletteModal` layers directly above the dialog (`z-index: 10000`), does not corrupt or close the underlying modal, and upon pressing `Escape`, returns focus safely to the active dialog.

---

## 2. Tester Brief
The tester (human or AI agent) will open the What's New modal via the sidebar footer (`.foot-btn[data-action="whats-new"]`), verify that it is mounted in `#modalHolder`, dispatch the `⌘K` keyboard accelerator, assert that `#cmdPaletteModal` opens with `z-index: 10000` above the What's New modal, press `Escape`, verify that the palette closes, and assert that the What's New modal remains active with focus restored to its close button.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** What's New modal open in `#modalHolder`
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[UNDERLYING_MODAL]`: Selector for base modal (`.whatsnew-modal`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Command Palette - Layered Modal Stacking and Z-Index Hierarchy

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    When the user clicks the footer button ".foot-btn[data-action='whats-new']"
    Then the What's New modal ".whatsnew-modal" should be mounted in "#modalHolder"

  @modals @stacking @z-index @focus @positive
  Scenario: Command palette layers above active modal without destroying underlying dialog
    When the user presses the shortcut "Meta+K"
    Then the command palette modal "#cmdPaletteModal" should be mounted
    And the computed z-index of "#cmdPaletteModal" should be 10000
    And the underlying modal ".whatsnew-modal" should still exist in "#modalHolder"
    And the active element should be "#cmdPaletteInput"

    When the user presses the "Escape" key
    Then the command palette modal "#cmdPaletteModal" should be removed from the DOM
    And "window.state.commandPalette.isOpen" should equal false
    And the underlying modal ".whatsnew-modal" should still be visible and open
    And focus should return to an interactive element within ".whatsnew-modal"
```

---

## 5. Visual Checks
- **Stacking Visuals:**
  - Command palette appears clearly superimposed over the darkened What's New modal backdrop.
  - Backdrop blur covers the underlying dialog.
- **Underlying Modal Preservation:**
  - Underlying modal does not shift position or lose rendered content.

---

## 6. Data & Network Checks
- **Computed Z-Index Assertions:**
  ```javascript
  const cmdModal = document.getElementById('cmdPaletteModal');
  const whatsNew = document.querySelector('.whatsnew-modal');
  assert(cmdModal !== null && whatsNew !== null, "Both modals must exist concurrently");
  const zIndex = parseInt(window.getComputedStyle(cmdModal).zIndex, 10);
  assert(zIndex >= 10000, "Command palette z-index must be at least 10000");
  ```
- **Post-Escape Assertions:**
  ```javascript
  assert(document.getElementById('cmdPaletteModal') === null, "Command palette must be unmounted");
  assert(document.querySelector('.whatsnew-modal') !== null, "Underlying modal must remain mounted");
  assert(whatsNew.contains(document.activeElement), "Focus must remain inside underlying modal");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-modal-stacking-and-z-index-layering/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of stacked modals, z-index measurements, and focus trace.
  - `evidence.json`: Captured z-index styles and activeElement hierarchies.
  - `screenshots/09-stacked-modals.png`: Command palette layered over What's New modal.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/cmd/case-09-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
