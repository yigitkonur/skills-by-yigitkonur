# Test Case: Brand Switcher Adversarial Search, Turkish Case-Folding & Empty State Retention

## 1. Case ID & Purpose
- **Case ID:** `TC-NAV-09-BRAND-SEARCH-TURKISH-EMPTY`
- **Purpose:** Verify brand switcher popover search resilience against adversarial inputs, ensuring that negative/zero-result queries hide all asset rows while safely retaining the exit link (`.all`) and group header without crashing, that Turkish diacritic case-folding (`"ÜLKER"` / `"ülker"`) correctly matches target brands, and that clicking outside the popover dismisses it cleanly.

---

## 2. Tester Brief
The tester (human or AI agent) will open the brand switcher popover (`.side-asset`), enter a non-existent search query (`"nonexistent999xyz"`), assert that all brand rows receive `display: none` but `.all[data-action="goto-home"]` remains visible, clear the input and type Turkish search strings (`"ülker"` and `"ÜLKER"`), assert that `data-slug="ulker"` matches in both cases, and click on `.main` outside the popover to assert that `#assetPop` gains `.hidden`.

---

## 3. Inputs & Prerequisites
- **Target URL:** `[APP_URL]/#/[SLUG]/overview`
- **Initial State:** Brand switcher popover `#assetPop` is opened
- **Placeholders Used:**
  - `[DOMAIN]`: Base domain under test
  - `[NEGATIVE_QUERY]`: Arbitrary non-matching string (`nonexistent999xyz`)
  - `[TURKISH_QUERY]`: Turkish diacritic queries (`ülker`, `ÜLKER`)
  - `[EXPECTED_SLUG]`: Target matched brand slug (`ulker`)

---

## 4. Gherkin Scenario

```gherkin
Feature: Brand Switcher - Adversarial Search, Turkish Case-Folding & Backdrop Dismissal

  Background:
    Given the user is on "[APP_URL]/#/[SLUG]/overview"
    When the user clicks the brand switcher trigger ".side-asset"
    Then the brand switcher popover "#assetPop" should be visible

  @negative @search @resilience
  Scenario: Non-matching search query hides all brand rows but preserves exit paths
    When the user types "nonexistent999xyz" into the search input ".asset-pop .search input"
    Then all brand rows ".asset-pop .row" should have style display "none"
    And the group header ".asset-pop .group-label" should remain in the DOM
    And the all assets link ".asset-pop .all[data-action='goto-home']" should remain visible

  @turkish @localization @case-folding @positive
  Scenario Outline: Turkish uppercase and lowercase diacritic searches match target brands
    When the user clears the search input ".asset-pop .search input"
    And the user types "<query>" into the search input ".asset-pop .search input"
    Then the brand row for data-slug "<expected_slug>" should be visible
    And the label of the visible row should contain "<expected_label>"

    Examples:
      | query  | expected_slug | expected_label |
      | ülker  | ulker         | Ülker          |
      | ÜLKER  | ulker         | Ülker          |
      | Ülker  | ulker         | Ülker          |

  @dismissal @backdrop @positive
  Scenario: Clicking outside the brand switcher popover dismisses the dropdown
    When the user clicks the main viewport area ".main"
    Then the popover container "#assetPop" should receive class "hidden"
```

---

## 5. Visual Checks
- **Zero-Result Layout:**
  - When all rows are hidden, the popover remains neat with the search input on top and the `.all` button at the bottom.
  - No broken layout or zero-height collapsed popover.
- **Turkish Match:**
  - Matching row highlights normally, displaying favicon and `"Ülker"` typography.
- **Backdrop Dismissal:**
  - Popover disappears immediately upon clicking outside without delay or ghost outlines.

---

## 6. Data & Network Checks
- **DOM Assertions:**
  ```javascript
  const pop = document.getElementById('assetPop');
  const rows = Array.from(pop.querySelectorAll('.row'));
  const visibleRows = rows.filter(r => r.style.display !== 'none');
  
  // Zero result check
  if (query === 'nonexistent999xyz') {
    assert(visibleRows.length === 0, "No rows should be visible");
    assert(pop.querySelector('.all') !== null, "All assets link must remain visible");
  }
  
  // Turkish match check
  if (query.toLowerCase() === 'ülker') {
    assert(visibleRows.length >= 1, "At least one row should match");
    assert(visibleRows[0].getAttribute('data-slug') === 'ulker', "Matched slug must be ulker");
  }
  
  // Backdrop check
  assert(pop.classList.contains('hidden'), "Popover must have hidden class after outside click");
  ```

---

## 7. Evidence & Reporting
- **Matching Result Directory:** `01-gherkin-result-case-brand-search-turkish-and-zero-results/`
- **Required Artifacts:**
  - `result.md`: Evaluation log covering empty results, Turkish case variants, and backdrop dismissal.
  - `evidence.json`: Filter counts and DOM visibility states.
  - `screenshots/09-brand-search-empty.png`: Popover with zero matching rows and visible exit button.
  - `screenshots/09-brand-search-turkish.png`: Matched Ülker row for Turkish query.
- **MacBook Execution Protocol:** Ego Browser captures display screenshots to `/tmp/ego-shots/nav/case-09-*.png` on the MacBook host, retrieved via SCP before compiling `result.md`.
