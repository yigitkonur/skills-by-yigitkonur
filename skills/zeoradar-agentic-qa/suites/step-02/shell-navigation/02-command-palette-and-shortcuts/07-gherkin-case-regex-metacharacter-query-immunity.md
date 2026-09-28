# Test Case: Adversarial Regex Metacharacters and Syntax Crash Immunity

## 1. Case ID & Purpose
- **Case ID:** `TC-CMD-07-REGEX-CHAR-IMMUNITY`
- **Purpose:** Verify search query sanitization within the Command Palette, ensuring that user inputs containing regular expression metacharacters (`[`, `]`, `*`, `+`, `?`, `^`, `$`, `\`, `(`, `)`, `{`, `}`, `|`) do not cause JavaScript syntax crashes (`SyntaxError: Invalid regular expression`), as matching is executed strictly via `String.prototype.indexOf`, and cleanly render the empty state `.cmd-empty`.

---

## 2. Tester Brief
The tester (human or AI agent) will open the command palette, enter hostile query strings packed with regex metacharacters (`"[[*+?^${}()|\\/]]"`, `"*(.*)+?"`), assert that the application continues running without console errors, verify that `getCmdItems()` evaluates safely, and assert that the empty state container `.cmd-empty` displays gracefully.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Command palette opened
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[ADVERSARIAL_QUERY]`: String containing regex metacharacters (`[[*+?^${}()|\/]]`, `*(.*)+?`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Command Palette - Adversarial Regex Metacharacter Immunity

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the command palette is open

  @adversarial @security @regex @resilience
  Scenario Outline: Typing regex metacharacters does not throw SyntaxError and renders empty state
    When the user types "<adversarial_query>" into the command palette input "#cmdPaletteInput"
    Then no JavaScript "SyntaxError" should be thrown
    And the rendered command items list should be empty
    And the empty state container ".cmd-empty" should be visible
    And the search input should retain the exact string "<adversarial_query>"

    Examples:
      | adversarial_query   |
      | [[*+?^${}()|\/]]    |
      | *(.*)+?             |
      | [a-z0-9]++          |
      | (?<=foo)bar         |
      | \\\\\\\\\\          |
```

---

## 5. Visual Checks
- **Empty State Presentation:**
  - `.cmd-empty` container displays search icon and localized text (`"No results found."` or `"Sonuç bulunamadı."`).
  - Modal structure remains intact without distortion or broken layout.

---

## 6. Data & Network Checks
- **Console & DOM Assertions:**
  ```javascript
  const emptyEl = document.querySelector('.cmd-empty');
  const items = document.querySelectorAll('.cmd-item');
  assert(emptyEl !== null, ".cmd-empty element must be displayed");
  assert(items.length === 0, "No command items should be displayed");
  ```
- **Error Tracking:**
  - Zero unhandled error events recorded on `window`.

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-regex-metacharacter-query-immunity/`
- **Required Artifacts:**
  - `result.md`: Evaluation log confirming crash immunity for all regex strings.
  - `evidence.json`: Captured error listener logs and DOM tree snapshots.
  - `screenshots/07-regex-empty-state.png`: View showing `.cmd-empty` with regex input.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/cmd/case-07-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
