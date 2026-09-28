# Test Case: Localized Zero-Result Empty State and Safe Enter Key Guard

## 1. Case ID & Purpose
- **Case ID:** `TC-CMD-08-EMPTY-STATE-ENTER-GUARD`
- **Purpose:** Verify the zero-result empty state behavior in the Command Palette, ensuring proper bilingual localization of the empty message (`"No results found."` in English, `"Sonuç bulunamadı."` in Turkish), and assert that pressing the `Enter` key while the item list is empty executes a safe zero-op guarded by `if (items[selIdx])`, preventing runtime `TypeError` crashes and preserving the open modal.

---

## 2. Tester Brief
The tester (human or AI agent) will open the command palette, enter an unmatched query (`"xyz123nonexistent"`), verify that `.cmd-empty` displays `"No results found."`, switch app language to Turkish (`state.lang = "tr"`), verify that the message translates to `"Sonuç bulunamadı."`, press the `Enter` key with the empty state visible, and assert that the palette remains open without throwing a JavaScript error.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Command palette opened
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[UNMATCHED_QUERY]`: String matching 0 commands (`xyz123nonexistent`)
  - `[LANGUAGE]`: Target language code (`en`, `tr`)
  - `[EXPECTED_MESSAGE]`: Localized text (`No results found.`, `Sonuç bulunamadı.`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Command Palette - Zero-Result Empty State and Enter Key Guard

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the command palette is open

  @empty-state @localization @positive
  Scenario Outline: Zero-result queries display properly localized empty state messages
    Given the application language is set to "<lang>"
    When the user types "xyz123nonexistent" into "#cmdPaletteInput"
    Then the empty state container ".cmd-empty" should be visible
    And the empty state text should equal "<expected_message>"

    Examples:
      | lang | expected_message    |
      | en   | No results found.   |
      | tr   | Sonuç bulunamadı.   |

  @enter-guard @resilience @positive
  Scenario: Pressing Enter on an empty result list performs a safe no-op
    When the user types "xyz123nonexistent" into "#cmdPaletteInput"
    And the empty state container ".cmd-empty" is displayed
    When the user presses the "Enter" key
    Then no JavaScript exception should be thrown
    And the command palette modal "#cmdPaletteModal" should remain open
    And "window.state.commandPalette.isOpen" should still equal true
```

---

## 5. Visual Checks
- **Empty State Display:**
  - Clean layout containing centered search SVG icon, margin spacing, and readable font.
  - No broken borders or visual glitch.

---

## 6. Data & Network Checks
- **Guard Assertions:**
  ```javascript
  const modal = document.getElementById('cmdPaletteModal');
  const emptyEl = document.querySelector('.cmd-empty');
  assert(modal !== null, "Modal must remain open after pressing Enter on empty list");
  assert(emptyEl !== null, "Empty state element must exist");
  assert(window.state.commandPalette.isOpen === true, "isOpen must remain true");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-empty-state-and-enter-guard/`
- **Required Artifacts:**
  - `result.md`: Evaluation log covering localized strings and Enter key guard validation.
  - `evidence.json`: Captured message strings and modal state.
  - `screenshots/08-empty-state-en.png`: English empty state view.
  - `screenshots/08-empty-state-tr.png`: Turkish empty state view.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/cmd/case-08-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
