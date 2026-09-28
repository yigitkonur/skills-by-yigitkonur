# Test Case: Command Execution via Enter Key and Direct Mouse Click Dispatch

## 1. Case ID & Purpose
- **Case ID:** `TC-CMD-04-COMMAND-EXECUTION`
- **Purpose:** Verify that activating a command within the palette—either by pressing `Enter` on the currently selected item or by directly clicking any `.cmd-item[data-action="select-cmd-item"]` with the mouse—successfully executes the associated action (`item.action()`), automatically closes and removes `#cmdPaletteModal`, updates `window.state.commandPalette.isOpen = false`, and transitions the application to the requested tab, workspace, or preference state.

---

## 2. Tester Brief
The tester (human or AI agent) will open the command palette, filter for `"opportunities"`, press the `Enter` key, verify that the palette closes and navigation transitions to `/[SLUG]/opportunities`, reopen the palette, navigate or click directly on `"Overview Dashboard"`, assert that the palette closes, and verify that navigation transitions back to the overview dashboard.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Brand `"[SLUG]"`, command palette opened
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[SEARCH_QUERY]`: Search filter used to surface command (`opportunities`, `overview`)
  - `[EXPECTED_TAB]`: Target tab after command execution (`opportunities`, `overview`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Command Palette - Command Execution via Keyboard Enter and Mouse Click

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the command palette is open

  @execution @keyboard @enter @positive
  Scenario: Pressing Enter on selected item executes command and dismisses palette
    When the user types "opportunities" into "#cmdPaletteInput"
    And the first item is selected with title "Top Opportunities"
    When the user presses the "Enter" key
    Then the command palette modal "#cmdPaletteModal" should be removed from the DOM
    And "window.state.commandPalette.isOpen" should equal false
    And "window.state.tab" should equal "opportunities"
    And the URL path should update to "/[SLUG]/opportunities"
    And the opportunities container ".opps-container" should be mounted

  @execution @mouse @click @positive
  Scenario: Clicking a command item directly executes command and dismisses palette
    Given the user is on "[APP_URL]/#/[SLUG]/opportunities"
    When the user opens the command palette via shortcut "Meta+K"
    And the user clicks the command item containing text "Overview Dashboard"
    Then the command palette modal "#cmdPaletteModal" should be removed from the DOM
    And "window.state.commandPalette.isOpen" should equal false
    And "window.state.tab" should equal "overview"
    And the URL path should update to "/[SLUG]"
```

---

## 5. Visual Checks
- **Immediate Dismissal:**
  - Modal overlay vanishes instantly without residual frozen backdrops.
- **View Mounting:**
  - Destination view renders completely with all headers, filters, and cards.

---

## 6. Data & Network Checks
- **Execution Invariants:**
  ```javascript
  assert(document.getElementById('cmdPaletteModal') === null, "Modal DOM must be removed");
  assert(window.state.commandPalette.isOpen === false, "isOpen must be false");
  assert(window.state.tab === '<expected_tab>', "Target tab must be activated");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-command-execution-enter-and-click/`
- **Required Artifacts:**
  - `result.md`: Trace of keyboard Enter and mouse click command executions.
  - `evidence.json`: State transitions from palette execution.
  - `screenshots/04-executed-destination.png`: Viewport showing target tab mounted after command.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/cmd/case-04-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
