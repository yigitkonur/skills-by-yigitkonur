# Test Case: Arrow Key Cycling (Up/Down), Selection Wrapping and Viewport Scrolling

## 1. Case ID & Purpose
- **Case ID:** `TC-CMD-03-ARROW-TRAVERSAL-WRAP`
- **Purpose:** Verify keyboard navigation mechanics within the Command Palette list, ensuring that pressing `ArrowDown` and `ArrowUp` updates `window.state.commandPalette.selectedIndex`, transfers the `.selected` class sequentially between items, wraps circularly across boundaries (index 0 wraps to bottom, last index wraps to 0), and auto-scrolls the scrollable container (`.cmd-body`, `max-height: 380px`) as items beyond the fold are highlighted.

---

## 2. Tester Brief
The tester (human or AI agent) will open the command palette without entering a search filter (15+ total items displayed), assert that initial `selectedIndex` is 0, press `ArrowDown` repeatedly, assert that `.cmd-item.selected` advances sequentially and `.cmd-body` scrolls downward, press `ArrowUp` to return upward, test boundary wrap-around by pressing `ArrowUp` from index 0 to reach the last item, and verify wrap-around from the bottom to the top.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Command palette open, unfiltered item registry (15+ items)
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[KEY_PRESS]`: Arrow key navigation events (`ArrowDown`, `ArrowUp`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Command Palette - Arrow Key Traversal, Circular Wrapping and Scrolling

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the command palette is open with 15 or more items
    And "window.state.commandPalette.selectedIndex" is 0

  @keyboard @navigation @scrolling @positive
  Scenario: Pressing ArrowDown navigates sequentially down the list and auto-scrolls container
    When the user presses the "ArrowDown" key 5 times
    Then "window.state.commandPalette.selectedIndex" should equal 5
    And the element '.cmd-item[data-idx="5"]' should have class "selected"
    And the element '.cmd-item[data-idx="0"]' should not have class "selected"
    And the container ".cmd-body" should adjust its scrollTop to keep the selected item in view

  @keyboard @boundary @wraparound @positive
  Scenario: Boundary wrap-around cycles seamlessly between top and bottom items
    Given the selected item index is 0
    When the user presses the "ArrowUp" key 1 time
    Then "window.state.commandPalette.selectedIndex" should equal the last item index
    And the last item in the list should receive class "selected"
    When the user presses the "ArrowDown" key 1 time
    Then "window.state.commandPalette.selectedIndex" should wrap around back to 0
    And the first item in the list should receive class "selected"
```

---

## 5. Visual Checks
- **Selection Visual:**
  - Active item displays prominent `.selected` highlight.
- **Scroll Behavior:**
  - `.cmd-body` smoothly scrolls to keep the selected row within the visible box (`max-height: 380px`).
  - No clipping or item obscurity beneath the header or bottom edge.

---

## 6. Data & Network Checks
- **Index Math Verification:**
  ```javascript
  const state = window.state.commandPalette;
  const items = document.querySelectorAll('.cmd-item');
  const selItem = document.querySelector('.cmd-item.selected');
  
  assert(parseInt(selItem.getAttribute('data-idx'), 10) === state.selectedIndex, "data-idx must equal state.selectedIndex");
  assert(state.selectedIndex >= 0 && state.selectedIndex < items.length, "Index must remain in bounds");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-arrow-traversal-and-wraparound/`
- **Required Artifacts:**
  - `result.md`: Audit of arrow traversal sequences, index values, and scroll metrics.
  - `evidence.json`: Captured `selectedIndex` logs and `scrollTop` measurements.
  - `screenshots/03-arrow-scrolled-item.png`: View of scrolled command palette highlighting deeper items.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/cmd/case-03-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
