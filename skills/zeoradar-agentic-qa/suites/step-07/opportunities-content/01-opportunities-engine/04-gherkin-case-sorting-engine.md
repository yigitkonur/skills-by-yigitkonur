# Test Case: TC-OPP-04 - Opportunities Sorting Engine

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-04`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenario `TC-OPP-05` (Sorting by Impact, Score, Type)
- **Purpose:** Validate that the Opportunities sorting popover enables the user to re-order the backlog by Impact Score (`impact`, default descending order), Performance Score (`score`), and Strategic Category Type (`type`), asserting that cards are correctly sorted in DOM and that sorting preserves card attributes and interactions.

---

## 2. Tester Brief
The tester will verify the sorting logic and UI indicators:
1. By default, the backlog is sorted descending by `impactScore` ($\ge 75$ high impact cards appear first).
2. Clicking the sort trigger button `.opps-btn-drop[data-pop="sort"]` opens the sort popover `.spop`.
3. Selecting "Opportunity Score" (`score`) sorts cards primarily by current performance or citation score.
4. Selecting "Strategy Type" (`type`) groups cards alphabetically or taxonomically by category (`content`, `outreach`, `reddit`).
5. Re-selecting "Impact Score" (`impact`) restores the default high-to-low impact score sequence.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Sort Modes Tested:** `impact`, `score`, `type`
- **Matching Result Directory:** `04-gherkin-result-case-sorting-engine/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Backlog Sorting by Impact, Performance Score, and Strategy Type

  Background:
    Given the user is viewing the Opportunities backlog for "[DOMAIN]"
    And the backlog contains at least 3 opportunity cards with varying scores and categories
    When the user clicks the Sort dropdown button "[data-action='opp-toggle-pop'][data-pop='sort']"
    Then the sort popover should open showing options "Impact Score", "Performance Score", "Strategy Type"

  Scenario Outline: Re-ordering Backlog by Selected Sort Criterion
    When the user selects the sort option "<SortOption>" with data-val "<SortVal>"
    Then the sort popover should close
    And the rendered opportunity cards should be ordered according to "<OrderingRule>"
    And the first rendered card should satisfy "<FirstCardAssertion>"

    Examples:
      | SortOption        | SortVal | OrderingRule                     | FirstCardAssertion                                   |
      | Impact Score      | impact  | impactScore descending           | impact score >= all subsequent cards in the backlog  |
      | Performance Score | score   | performanceScore ascending/order | lowest performance gap or highest citation indicator |
      | Strategy Type     | type    | category alphabetical grouping   | cards with identical category appear clustered       |

  Scenario: Default Sort Persistence
    Given the user opens the Opportunities page fresh
    Then the default sort should be "impact"
    And cards with impact score in High tier (75-100) should occupy top positions
```

---

## 5. Visual Checks
1. **Sort Popover:** `.spop` renders cleanly below the sort button with checkmark indicating current sort selection.
2. **Order of Elements:** Inspect `.op-card` order; verify impact badges (`.op-impact-val`) follow non-ascending sequence when sorted by `impact`.
3. **Button Label:** The sort trigger button updates its label or tooltip to reflect the selected sort mode (e.g. `Sort: Impact` or `Sırala: Etki`).

---

## 6. Data and Network Checks
1. **Config State:**
   - Verify `window.state.oppsConfig.sortBy` updates to `"impact"`, `"score"`, or `"type"`.
2. **Sorting Logic Inspection:**
   ```js
   var sortedCards = Array.from(document.querySelectorAll('.op-card')).map(card => ({
     id: card.dataset.opid,
     impact: parseInt(card.querySelector('.op-impact-val')?.innerText || '0', 10),
     category: card.className.match(/op-card-(\w+)/)?.[1]
   }));
   // When sorted by impact:
   for (let i = 0; i < sortedCards.length - 1; i++) {
     console.assert(sortedCards[i].impact >= sortedCards[i + 1].impact, "Card " + i + " impact violates descending order");
   }
   ```

---

## 7. Evidence and Reporting
- **Target Result Directory:** `04-gherkin-result-case-sorting-engine/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `sort_menu_open.png` showing the sort popover options.
  2. Capture `sorted_by_impact.png` proving descending impact score sequence.
  3. Capture `sorted_by_type.png` showing categorized card clustering.
  4. Transfer screenshots from MacBook:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-sort/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/04-gherkin-result-case-sorting-engine/
     ```
  5. Log validation results in `result.md`.

### Pass/Fail Criteria
- [ ] Sort popover opens and closes reliably without event collision.
- [ ] Sorting by `impact` strictly orders all visible cards descending by impact score.
- [ ] Card click handlers and action button delegation remain fully intact after re-ordering.
