# Case 02: Turkish Diacritic Normalization & Intent-Grouped Autocomplete

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-02`
- **Purpose**: Verify that the Universal Search Autocomplete engine (`volGetSemanticSuggestions`) uses locale-aware `.toLocaleLowerCase("tr")` case folding to accurately normalize Turkish uppercase characters and diacritics (`Ç`, `İ`, `ı`, `ş`, `ğ`, `ü`, `ö`), prevents Latin ASCII character corruption (such as combining-dot bugs on dotted `İ` or dotless `I`), clusters real-time suggestions under 4 intent headers (Informational, Commercial, Transactional, Navigational) capped at 3 items per cluster, and updates the active keyword upon item selection.

## 2. Tester Brief
The tester inputs various Turkish search queries containing uppercase diacritics into `#volUniversalSearchInput` (e.g. `"KLİMA"`, `"İNDİRİM"`, `"ISI POMPASI"`, `"ŞOFBEN"`). The tester verifies that the search dropdown `#volUniversalDropHost .volumes-search-dropdown` opens, that suggestions are correctly categorized under intent headers, that each intent cluster displays at most 3 items, that dotted `İ` and dotless `I` match without character corruption, and that clicking a suggestion applies the term and closes the dropdown.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Test Queries: `"KLİMA"`, `"İNDİRİM"`, `"ISI POMPASI"`, `"ŞOFBEN"`
  - Locale: Turkish (`tr-TR` / `tr`)
- **Prerequisites**:
  - Prompt Volumes page loaded.

## 4. Gherkin Scenario

```gherkin
Feature: Semantic Autocomplete with Turkish Diacritic Integrity
  As a Global Search Analyst
  I want search autocomplete to handle Turkish diacritics and intent grouping accurately
  So that Turkish language consumer queries are normalized without Unicode corruption

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    And the Universal Search Input "#volUniversalSearchInput" is ready for input

  Scenario Outline: Query autocomplete with uppercase Turkish diacritics
    When the user types query "<input_query>" into "#volUniversalSearchInput"
    Then the autocomplete dropdown ".volumes-search-dropdown" should appear
    And the query should be normalized to "<normalized_target>" using Turkish locale casing
    And the suggestions should be clustered under at least one intent section:
      | .vol-drop-sec |
    And each visible intent cluster should contain at most 3 suggestion items ".vol-drop-item"
    And each suggestion item should display a positive numeric volume

    Examples:
      | input_query | normalized_target |
      | KLİMA       | klima             |
      | İNDİRİM     | indirim           |
      | ISI POMPASI | ısı pompası       |
      | ŞOFBEN      | şofben            |

  Scenario: Select autocomplete suggestion and update workspace keyword
    Given the autocomplete dropdown is displayed for query "klima"
    When the user clicks the first suggestion item ".vol-drop-item"
    Then the autocomplete dropdown should dismiss cleanly
    And the search input value should update to the selected term
    And the prompt table or keyword workspace should reflect the selected term
```

## 5. Visual Checks
- **Dropdown Styling**: High z-index popup (`.volumes-search-dropdown`) with rounded border, card shadow, and backdrop.
- **Intent Section Headers**: `.vol-drop-title` displays small uppercase text with icon indicating intent.
- **Item Hover**: Smooth background highlight on hover with subtle transition.

## 6. Data and Network Checks
- **Normalization Integrity Assertion**:
  ```javascript
  const prof = window.volActiveProfile();
  const resDotted = window.volGetSemanticSuggestions("KLİMA", prof);
  const resDotless = window.volGetSemanticSuggestions("ISI POMPASI", prof);
  assert.ok(Object.keys(resDotted).some(k => resDotted[k].length > 0));
  assert.ok(Object.keys(resDotless).some(k => resDotless[k].length > 0));
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-turkish-diacritic-semantic-autocomplete/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-02-autocomplete-turkish.png`
     - `/tmp/ego-shots/tc-vol-02-intent-clusters.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-02-*.png ./02-gherkin-result-case-turkish-diacritic-semantic-autocomplete/
     ```
