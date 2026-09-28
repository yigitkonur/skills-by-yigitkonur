# Test Case: Real-time Query Filtering across Titles and Categories with Caret Preservation

## 1. Case ID & Purpose
- **Case ID:** `TC-CMD-02-QUERY-FILTERING`
- **Purpose:** Verify real-time query filtering in the Command Palette as characters are typed into `#cmdPaletteInput`, ensuring matching operates across both item titles and category names (`it.title` and `it.category`), dynamically updates the displayed item count, resets `selectedIndex` to 0 on new input, and preserves input cursor selection range without jumping to the line end.

---

## 2. Tester Brief
The tester (human or AI agent) will open the command palette, type search queries (`"theme"`, `"opportunities"`, `"preferences"`), assert that matching commands are filtered down, verify that the first matching command receives the `.selected` class (`data-idx="0"`), inspect caret position during multi-character typing, and verify that partial matches across categories (e.g. `"Action"`) successfully return all member commands.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Command palette opened, `#cmdPaletteInput` focused
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[SEARCH_QUERY]`: Query string entered into the palette input
  - `[EXPECTED_MATCH_TITLE]`: First matched command title
  - `[EXPECTED_CATEGORY]`: Matched item category

---

## 4. Gherkin Scenario

```gherkin
Feature: Command Palette - Real-Time Query Filtering and Caret Preservation

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    And the command palette is open with active input focus

  @search @filtering @positive
  Scenario Outline: Typing queries filters command registry across titles and categories
    When the user types "<query>" into the command palette input "#cmdPaletteInput"
    Then "window.state.commandPalette.query" should equal "<query>"
    And the rendered command items count should equal "<expected_count>"
    And the first command item ".cmd-item[data-idx='0']" should have class "selected"
    And the first command item title should contain "<expected_title>"
    And the input selection caret position should be preserved at the end of the typed string

    Examples: Title Matches
      | query         | expected_count | expected_title         |
      | opportunities | 1              | Top Opportunities      |
      | theme         | 3              | Theme: Switch to       |
      | dashboards    | 1              | Custom Dashboards      |

    Examples: Category Matches
      | query         | expected_count | expected_title         |
      | preferences   | 4              | Theme: Switch to Light |
      | analytics     | 4              | Overview Dashboard     |
```

---

## 5. Visual Checks
- **Result Highlighting:**
  - First item in the filtered list is automatically highlighted with `.selected` styling (subtle accent background and left pill/bar indicator).
  - Category headers (`.cmd-group-title`) adjust to show only active groups containing matches.
- **Caret Stability:**
  - Cursor does not bounce or un-focus as DOM re-renders during input typing.

---

## 6. Data & Network Checks
- **Filter Assertions:**
  ```javascript
  const query = window.state.commandPalette.query;
  const items = Array.from(document.querySelectorAll('.cmd-item'));
  const firstItem = items[0];
  
  assert(items.length > 0, "Filtered items must not be empty for valid query");
  assert(firstItem.classList.contains('selected'), "First item must be selected");
  const title = firstItem.querySelector('.cmd-item-left span').textContent.toLowerCase();
  const cat = firstItem.querySelector('.cmd-item-cat').textContent.toLowerCase();
  assert(title.includes(query.toLowerCase()) || cat.includes(query.toLowerCase()), "Match must satisfy title or category");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-query-search-and-filtering/`
- **Required Artifacts:**
  - `result.md`: Evaluation log of filter queries, result counts, and response latency.
  - `evidence.json`: Captured item dumps for each query variant.
  - `screenshots/02-filter-theme.png`: Filtered results for query "theme".
  - `screenshots/02-filter-opps.png`: Filtered results for query "opportunities".
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/cmd/case-02-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
