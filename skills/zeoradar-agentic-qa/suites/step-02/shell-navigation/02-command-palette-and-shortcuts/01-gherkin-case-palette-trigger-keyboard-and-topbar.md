# Test Case: Palette Trigger via Keyboard Shortcuts (⌘K / Ctrl+K) and Topbar Button

## 1. Case ID & Purpose
- **Case ID:** `TC-CMD-01-PALETTE-TRIGGER`
- **Purpose:** Verify that the Command Palette can be invoked both via keyboard accelerators (`Meta+K` on macOS, `Ctrl+K` on Linux/Windows) and by clicking the topbar button (`.cmd-trigger-btn[data-action="open-cmd-palette"]`), ensuring that the modal container `#cmdPaletteModal` renders immediately, sets `state.commandPalette.isOpen = true`, and programmatically places active input focus onto `#cmdPaletteInput`.

---

## 2. Tester Brief
The tester (human or AI agent) will navigate to `[APP_URL]/#/[SLUG]/overview`, dispatch a `Meta+K` / `Ctrl+K` keyboard event, verify that `#cmdPaletteModal` opens and `#cmdPaletteInput` receives focus, dismiss the palette via Escape, click the topbar trigger button `.cmd-trigger-btn`, and assert that the palette reopens with active input focus and default categorized items.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** `state.commandPalette.isOpen === false`, modal holder `#cmdPaletteHolder` empty
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[KEYBOARD_SHORTCUT]`: Trigger shortcut (`Meta+K` / `Ctrl+K`)
  - `[TRIGGER_SELECTOR]`: Topbar button element (`.cmd-trigger-btn`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Command Palette - Invocation via Keyboard Shortcuts and Topbar Trigger

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the command palette is currently closed

  @keyboard @shortcut @positive
  Scenario Outline: Invoking palette via keyboard shortcut opens modal and focuses input
    When the user presses the keyboard shortcut "<shortcut>"
    Then the command palette modal "#cmdPaletteModal" should be mounted in the DOM
    And "window.state.commandPalette.isOpen" should equal true
    And the input element "#cmdPaletteInput" should have document focus
    And the category title ".cmd-group-title" should be visible

    Examples:
      | shortcut |
      | Meta+K   |
      | Ctrl+K   |

  @ui-trigger @positive
  Scenario: Clicking the topbar button opens the command palette
    Given the command palette is closed
    When the user clicks the topbar trigger button ".cmd-trigger-btn"
    Then the command palette modal "#cmdPaletteModal" should be mounted
    And "window.state.commandPalette.isOpen" should equal true
    And the input element "#cmdPaletteInput" should have document focus
```

---

## 5. Visual Checks
- **Backdrop & Modal Styling:**
  - `#cmdPaletteModal.cmd-backdrop` covers the viewport with semi-transparent frosted blur (`backdrop-filter: blur(12px)`).
  - Modal container `.cmd-modal` is vertically centered in the upper third of the screen with soft elevation shadow.
  - Search icon and ESC badge `<kbd class="cmd-kbd">ESC</kbd>` render crisply inside `.cmd-header`.
- **Active Focus:**
  - Search input `#cmdPaletteInput` displays caret cursor and active outline.

---

## 6. Data & Network Checks
- **DOM & State Assertions:**
  ```javascript
  const modal = document.getElementById('cmdPaletteModal');
  const input = document.getElementById('cmdPaletteInput');
  assert(modal !== null, "Modal container must be mounted");
  assert(window.state.commandPalette && window.state.commandPalette.isOpen === true, "state.commandPalette.isOpen must be true");
  assert(document.activeElement === input, "Active element must be #cmdPaletteInput");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-palette-trigger-keyboard-and-topbar/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of keyboard and mouse click open triggers.
  - `evidence.json`: Dump of `window.state.commandPalette` and focus element metadata.
  - `screenshots/01-palette-open-default.png`: Initial opened view of the command palette.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/cmd/case-01-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
