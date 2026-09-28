# Case 01: Universal Search Cockpit & Intent Filter Bar

## 1. Case ID and Purpose
- **Case ID**: `TC-VOL-01`
- **Purpose**: Verify that the Universal Search Cockpit on the Prompt Volumes page (`/#/app/:slug/volumes`) provides an accessible search input responding to the global `⌘K` shortcut, renders the 5 intent filter pills (`All Intents`, `Informational`, `Commercial`, `Transactional`, `Navigational`), and accurately filters the Top 25 consumer prompts table in real time without page reloads.

## 2. Tester Brief
The tester loads the Prompt Volumes module, checks that `#volUniversalSearchInput` is present with its `⌘K` shortcut badge, tests pressing `⌘K` to focus the search input, clicks each of the intent filter pills, and confirms that the prompt table rows update dynamically to display only prompts corresponding to the selected intent badge (e.g. `.vol-intent-trans`, `.vol-intent-info`). Finally, the tester clicks "All Intents" to restore the complete prompt catalog.

## 3. Inputs and Prerequisites
- **Inputs**:
  - `[DOMAIN]`: `[DOMAIN]`
  - Route: `[APP_URL]/#/[SLUG]/volumes`
  - Permitted Intent Keys: `all`, `info`, `comm`, `trans`, `nav`
- **Prerequisites**:
  - Application loaded on Prompt Volumes page.

## 4. Gherkin Scenario

```gherkin
Feature: Universal Search Cockpit & Intent-Based Prompt Filtering
  As a Search Intent Strategist
  I want to filter consumer search queries by specific intent categories
  So that I can evaluate transactional purchase queries separately from informational queries

  Background:
    Given the user navigates to "[APP_URL]/#/[SLUG]/volumes"
    And the page container ".volumes-analytics-page" is displayed
    And the Top 25 Consumer Prompts table ".vol-prompt-table" is rendered

  Scenario: Verify Universal Search Input and shortcut keybinding
    Then the search input "#volUniversalSearchInput" should be visible
    And the search container should display the shortcut badge ".vol-search-shortcut" with text "⌘K"
    When the user triggers key combination "Meta+K" or "Control+K"
    Then the search input "#volUniversalSearchInput" should receive keyboard focus

  Scenario Outline: Filter Top 25 prompts table by intent categories
    When the user clicks the intent pill "button.vol-intent-pill[data-intent='<intent_key>']"
    Then the intent pill for "<intent_key>" should have active class ".active"
    And "window.volumesState.intentFilter" should be set to "<intent_key>"
    And all visible prompt rows in ".vol-prompt-table" should render the intent badge "<expected_badge_class>"

    Examples:
      | intent_key | expected_badge_class |
      | trans      | .vol-intent-trans    |
      | comm       | .vol-intent-comm     |
      | info       | .vol-intent-info     |
      | nav        | .vol-intent-nav      |

  Scenario: Reset intent filtering to All Intents
    Given an intent filter is active
    When the user clicks the intent pill "button.vol-intent-pill[data-intent='all']"
    Then all prompt rows should be visible regardless of intent
    And "window.volumesState.intentFilter" should be "all"
```

## 5. Visual Checks
- **Search Box Layout**: Magnifying glass icon on left, clean placeholder text, and `⌘K` pill on the right.
- **Intent Pills**: Smooth transition between default muted pill styling and brand-accented `.active` state.
- **Intent Badges**: Distinct color-coding across badges (Accent for Info, Ink for Comm, Green for Trans, Muted Ink for Nav).

## 6. Data and Network Checks
- **State Property Synchronizations**:
  ```javascript
  assert.strictEqual(window.volumesState.activeTab, 'overview');
  assert.strictEqual(window.volumesState.intentFilter, 'trans');
  const rows = document.querySelectorAll('.vol-prompt-table tbody tr');
  rows.forEach(r => assert.ok(r.querySelector('.vol-intent-trans')));
  ```

## 7. Evidence and Reporting
- **Target Result Directory**: `02-gherkin-result-case-universal-search-and-intent-filters/`
- **Execution Model**:
  1. Automated test runs via `ego-browser nodejs` on MacBook host.
  2. Screenshots captured:
     - `/tmp/ego-shots/tc-vol-01-cockpit-default.png`
     - `/tmp/ego-shots/tc-vol-01-intent-trans.png`
  3. Transferred locally via SCP before compiling final report:
     ```bash
     scp macbook:/tmp/ego-shots/tc-vol-01-*.png ./02-gherkin-result-case-universal-search-and-intent-filters/
     ```
