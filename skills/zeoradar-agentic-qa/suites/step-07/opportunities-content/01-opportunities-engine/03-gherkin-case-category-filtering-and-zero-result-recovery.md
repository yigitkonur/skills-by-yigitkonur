# Test Case: TC-OPP-03 - Category Filtering & Zero-Result Empty State Recovery

## 1. Case ID and Purpose
- **Case ID:** `TC-OPP-03`
- **Module:** Opportunities Engine (`assets/opportunities.js`, `assets/opportunities.css`)
- **Parent Contract:** Issue #47 (PostgreSQL Opportunity Storage & Gap Analysis Pipeline)
- **Traceability:** Maps to Source Scenarios `TC-OPP-04` (Category Filtering) and `TC-OPP-18` (Category Filter Zero-Results Empty State & Reset Filter Recovery)
- **Purpose:** Test filtering the opportunities backlog by strategic category (`all`, `outreach`, `reddit`, `content`) via the filter dropdown popover, verify that when a selected category yields 0 matching opportunities an explicit empty state placeholder is rendered with a dedicated reset action, and confirm that clicking the reset CTA restores the full backlog to `"all"` immediately.

---

## 2. Tester Brief
The tester will validate category filtering and empty state resilience:
1. Opening the filter dropdown `.opps-btn-drop[data-pop="filter"]` displays options for `All`, `Outreach`, `Forum / Reddit`, and `Content Creation`.
2. Selecting a category filters the rendered cards so only items with that category appear.
3. When a selected filter matches zero items (e.g. if all cards in that category are archived or none exist in the scan), an empty state card (`.opps-list .opps-empty-state`) must be rendered with an informative message.
4. The empty state card must contain a prominent "Reset filters" button: `button.btn[data-action="opp-reset-filter"]`.
5. Clicking "Reset filters" sets `cfg.filterCategory = "all"`, closes any open popovers, and restores all active opportunity cards without requiring a page refresh.

---

## 3. Inputs and Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/opportunities`
- **Monitored Brand `[DOMAIN]`:** `[DOMAIN]`
- **Target Market `[COUNTRY]`:** `US`
- **UI Language `[LANGUAGE]`:** `en`
- **Filter Categories Tested `[OPP_TYPE]`:** `all`, `outreach`, `reddit`, `content`
- **Matching Result Directory:** `03-gherkin-result-case-category-filtering-and-zero-result-recovery/` *(Do not create ahead of test execution)*

---

## 4. Gherkin Scenario

```gherkin
Feature: Category Dropdown Filtering and Zero-Result Quick-Reset Recovery

  Background:
    Given the user is on the Opportunities page for "[DOMAIN]"
    And the active backlog contains mixed opportunity categories
    When the user clicks the filter dropdown button "[data-action='opp-toggle-pop'][data-pop='filter']"
    Then the filter popover ".fpop" should become visible with category options

  Scenario Outline: Filtering Backlog by Category
    When the user selects the filter option with value "<CategoryValue>"
    Then the popover should close
    And all rendered ".op-card" elements should match category "<CategoryValue>"
    And no cards of other categories should be visible

    Examples:
      | CategoryValue |
      | outreach      |
      | reddit        |
      | content       |

  Scenario: Zero-Result Category Filter and Quick-Reset Recovery Loop
    Given all opportunities of category "reddit" are archived or dismissed
    When the user filters the active backlog by category "reddit"
    Then zero ".op-card" elements should be rendered in ".opps-list"
    And an empty state card ".opps-empty-state" should be displayed inside ".opps-list"
    And the empty card should display message "No opportunities found matching this filter"
    And the empty card should display a reset button "button[data-action='opp-reset-filter']"
    
    When the user clicks the "Reset filters" button
    Then the active category filter should reset to "all"
    And the empty state card should be removed
    And the full backlog of active opportunity cards should be restored in ".opps-list"
```

---

## 5. Visual Checks
1. **Filter Popover:** `.fpop` opens positioned directly beneath the filter button, containing 4 `.opt` choices with checkmark indicators for the currently active choice.
2. **Category Isolation:**
   - When `reddit` is active, only amber-railed `.op-card-reddit` cards appear.
   - When `outreach` is active, only blue-railed `.op-card-outreach` cards appear.
   - When `content` is active, only pink-railed `.op-card-content` cards appear.
3. **Empty State Placeholder:**
   - Centered inside `.opps-list` with a subtle dashed or solid border card.
   - Displays empty search icon or illustration.
   - Renders localized title: `"No opportunities found matching this filter"` / `"Bu filtreyle eşleşen fırsat bulunamadı"`.
   - Renders action button: `button.btn.black.small[data-action="opp-reset-filter"]` with text `"Reset filters"` / `"Filtreleri sıfırla"`.

---

## 6. Data and Network Checks
1. **Config State:**
   - Inspect `window.state.oppsConfig.filterCategory`:
     - After selecting `reddit`: equals `"reddit"`.
     - After clicking reset: equals `"all"`.
2. **Backlog Integrity:**
   - Verify that filtering does not alter the underlying `window.state.opportunities` array, only the displayed subset.
3. **Pop State:**
   - Assert `window.state.oppsConfig.popOpen === null` after choosing an option or resetting.

---

## 7. Evidence and Reporting
- **Target Result Directory:** `03-gherkin-result-case-category-filtering-and-zero-result-recovery/`
- **MacBook / Ego Browser Capture Protocol:**
  1. Capture `filter_dropdown_open.png` showing the popover menu.
  2. Capture `filter_applied_reddit.png` showing filtered single-category cards.
  3. Capture `zero_result_empty_state.png` showing empty card with "Reset filters" CTA.
  4. Capture `filter_recovered_all.png` showing full restored backlog.
  5. Transfer screenshots:
     ```bash
     scp macbook:/tmp/ego-test/opportunities-filter/*.png .agents/skills/zeoradar-agentic-qa/suites/step-07/opportunities-content/01-opportunities-engine/03-gherkin-result-case-category-filtering-and-zero-result-recovery/
     ```
  6. Document verification findings in `result.md`.

### Pass/Fail Criteria
- [ ] Category dropdown options cleanly isolate designated card categories.
- [ ] Zero-result filtering displays dedicated empty state and does not leave a blank white area.
- [ ] Reset filter button restores `filterCategory = "all"` and re-renders full active backlog.
- [ ] No JavaScript errors occur when toggling filters repeatedly at high velocity.
